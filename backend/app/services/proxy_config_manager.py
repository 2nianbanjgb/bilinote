import json
import os
import threading
from pathlib import Path
from typing import Any, Dict, Optional

# 多个任务线程会同时读到/写回同一份配置（比如 yt-dlp 轮换 Cookie 后回写代理、
# Cookie 配置），写文件必须串行 + 原子替换，避免读到写了一半的 JSON。
_WRITE_LOCK = threading.Lock()


class ProxyConfigManager:
    """代理配置，存 JSON 文件，支持前端动态修改。

    两类代理：

    - 全局代理：作用于 LLM API + 转写 API（Groq 等）+ 各平台下载（兜底）。
    - YouTube 专用代理：YouTube 对机房 IP 的风控远严于其它平台，需要单独走住宅/
      非机房线路时配置它；其它平台（B 站、抖音）仍然直连。

    优先级：
      1. 配置文件中启用的全局代理 > 环境变量 HTTP_PROXY/HTTPS_PROXY/ALL_PROXY；
      2. YouTube 相关请求优先用 ``youtube_url``，没配才回落到全局代理。
    """

    def __init__(self, filepath: str = "config/proxy.json"):
        self.path = Path(filepath)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _read(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write(self, data: Dict[str, Any]):
        # 先写临时文件再原子替换：并发写时读侧永远不会看到半截 JSON
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with _WRITE_LOCK:
            tmp.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            os.replace(tmp, self.path)

    def get_config(self) -> Dict[str, Any]:
        data = self._read()
        return {
            "enabled": bool(data.get("enabled", False)),
            "url": data.get("url", "") or "",
            "youtube_url": data.get("youtube_url", "") or "",
        }

    def update_config(
        self,
        enabled: bool,
        url: Optional[str] = None,
        youtube_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        data = self._read()
        data["enabled"] = bool(enabled)
        if url is not None:
            data["url"] = url.strip()
        if youtube_url is not None:
            data["youtube_url"] = youtube_url.strip()
        self._write(data)
        return self.get_config()

    def get_proxy_url(self) -> Optional[str]:
        """返回当前生效的全局代理 URL；没有则 None。

        - 配置文件 enabled=true 且 url 非空 → 用配置的 url
        - 否则回退到环境变量（标准的 HTTP_PROXY / HTTPS_PROXY / ALL_PROXY，大小写都认）
        """
        cfg = self.get_config()
        if cfg["enabled"] and cfg["url"]:
            return cfg["url"]
        for key in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy", "ALL_PROXY", "all_proxy"):
            val = os.environ.get(key)
            if val:
                return val
        return None

    def get_youtube_proxy_url(self) -> Optional[str]:
        """YouTube 专用代理；没配专用代理时回落全局代理（保持旧行为）。"""
        cfg = self.get_config()
        if cfg["youtube_url"]:
            return cfg["youtube_url"]
        return self.get_proxy_url()

    def apply_to_env(self) -> Optional[str]:
        """把当前生效的全局代理 URL 写进进程环境变量，返回生效的 url（无则 None）。

        为什么需要（issue #417）：huggingface_hub / requests 这类库**只认**环境变量
        HTTP_PROXY / HTTPS_PROXY / ALL_PROXY，不读我们 UI 配置文件。whisper 模型用
        snapshot_download 从 HuggingFace 拉取，如果用户只在设置页填了代理，下载根本
        不走代理 —— 就是用户说的「Docker 容器里代理没生效」。在下载前/启动时调用本
        方法，把 UI 配的代理 export 到环境变量，HF 下载就能复用同一个代理。

        注意：环境变量是进程级的，没法按域名区分，所以这里只导出全局代理；
        YouTube 专用代理只作用于 YouTube 下载/字幕请求（见 youtube_downloader）。
        """
        url = self.get_proxy_url()
        if not url:
            return None
        for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
                    "http_proxy", "https_proxy", "all_proxy"):
            os.environ[key] = url
        return url
