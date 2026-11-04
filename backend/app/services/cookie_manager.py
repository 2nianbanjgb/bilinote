import json
import os
import threading
from pathlib import Path
from typing import Optional, Dict

# 任务线程池里多个任务可能同时回写 Cookie（yt-dlp 轮换后写回），写文件必须串行 +
# 原子替换，否则会写坏 JSON 让后续读取全部失败。
_WRITE_LOCK = threading.Lock()


class CookieConfigManager:
    def __init__(self, filepath: str = "config/downloader.json"):
        self.path = Path(filepath)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write({})

    def _read(self) -> Dict[str, Dict[str, str]]:
        try:
            with self.path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _write(self, data: Dict[str, Dict[str, str]]):
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        with _WRITE_LOCK:
            tmp.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            os.replace(tmp, self.path)

    def get(self, platform: str) -> Optional[str]:
        data = self._read()
        return data.get(platform, {}).get("cookie")

    def set(self, platform: str, cookie: str):
        data = self._read()
        data[platform] = {"cookie": cookie}
        self._write(data)

    def delete(self, platform: str):
        data = self._read()
        if platform in data:
            del data[platform]
            self._write(data)

    def list_all(self) -> Dict[str, str]:
        data = self._read()
        return {k: v.get("cookie", "") for k, v in data.items()}

    def exists(self, platform: str) -> bool:
        return self.get(platform) is not None
