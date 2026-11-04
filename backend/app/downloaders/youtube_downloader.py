import logging
import os
import random
import tempfile
import time
from abc import ABC
from typing import List, Optional, Tuple, Union

import yt_dlp

from app.downloaders.base import Downloader, DownloadQuality, YDL_RETRY_OPTS
from app.downloaders.youtube_subtitle import YouTubeSubtitleFetcher
from app.models.notes_model import AudioDownloadResult
from app.models.transcriber_model import TranscriptResult
from app.services.cookie_manager import CookieConfigManager
from app.services.proxy_config_manager import ProxyConfigManager
from app.utils.path_helper import get_data_dir
from app.utils.url_parser import extract_video_id

logger = logging.getLogger(__name__)

# YouTube 反爬 / 限流时 yt-dlp 抛出的典型文案。命中这些字样说明重试有意义，
# 但也说明当前出口 IP 或 Cookie 已经不被 YouTube 信任，需要退避一段时间。
_ANTI_BOT_MARKERS = (
    "sign in to confirm",
    "not a bot",
    "http error 429",
    "too many requests",
)

_YOUTUBE_BLOCKED_HINT = (
    "YouTube 拒绝了本次下载（反爬/限流）：出口 IP 被判定为机器人，或保存的 Cookie 已失效。\n"
    "建议：1) 在「设置 → 代理」给 YouTube 单独配置住宅/非机房节点；"
    "2) 重新导出 YouTube Cookie（登录态）后再试；"
    "3) 等 10 分钟以上再试——立即重试只会继续累加限流。"
)


class YouTubeAccessBlockedError(RuntimeError):
    """YouTube 反爬/限流拒绝了请求。异常消息可直接展示给用户。"""


def _is_anti_bot_error(exc: BaseException) -> bool:
    text = str(exc).lower()
    return any(marker in text for marker in _ANTI_BOT_MARKERS)


def _split_cookie_header(cookie: str) -> List[Tuple[str, str]]:
    """把 `a=1; b=2` 形式的 Cookie 头拆成 (name, value) 列表。"""
    pairs: List[Tuple[str, str]] = []
    for part in cookie.split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name, value = part.split("=", 1)
        name = name.strip()
        if name:
            pairs.append((name, value))
    return pairs


def _to_netscape(cookie: str) -> str:
    """把 Cookie 头转成 yt-dlp 能读的 Netscape 格式。"""
    lines = ["# Netscape HTTP Cookie File", ""]
    for name, value in _split_cookie_header(cookie):
        lines.append(
            "\t".join([".youtube.com", "TRUE", "/", "TRUE", "2147483647", name, value])
        )
    return "\n".join(lines) + "\n"


def _read_netscape(path: str) -> List[Tuple[str, str]]:
    """从 yt-dlp 回写后的 Netscape 文件里读回 Cookie（跳过已过期的条目）。

    注意 `#HttpOnly_` 前缀：yt-dlp 用 ``#HttpOnly_.youtube.com`` 表示 HttpOnly
    Cookie（SID / HSID / SSID / APISID / SAPISID / LOGIN_INFO ...）。这些恰好是登录
    态的核心凭据，绝不能当成注释行丢掉，否则回写配置时会把登录 Cookie 洗没。
    """
    pairs: List[Tuple[str, str]] = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.rstrip("\r\n")
                if line.startswith("#HttpOnly_"):
                    line = line[len("#HttpOnly_"):]
                elif not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) < 7:
                    continue
                domain, _flag, _path, _secure, expiry, name, value = parts[:7]
                if not name or ("youtube.com" not in domain and "google.com" not in domain):
                    continue
                try:
                    expires_at = int(expiry)
                except ValueError:
                    expires_at = 0
                if expires_at and expires_at < time.time():
                    continue
                pairs.append((name, value))
    except OSError:
        return []
    return pairs


def _apply_proxy(ydl_opts: dict) -> dict:
    """YouTube 需要代理时可以单独配置，其它平台直连。

    这里只取 YouTube 专用代理（没配则回落到全局代理），B 站 / 抖音的下载器
    不会读到它，也就不会被 YouTube 的线路拖慢。
    """
    proxy = ProxyConfigManager().get_youtube_proxy_url()
    if proxy:
        ydl_opts["proxy"] = proxy
        logger.info(f"yt-dlp 走 YouTube 代理: {proxy}")
    return ydl_opts


class YoutubeDownloader(Downloader, ABC):
    def __init__(self):

        super().__init__()
        self._cookiefile: Optional[str] = None
        self._cookie_snapshot: Optional[str] = None

    # ---------------- Cookie 文件管理 ----------------
    def _ensure_cookie_file(self, force: bool = False) -> Optional[str]:
        """确保存在与当前配置一致的临时 Cookie 文件。

        配置里的 Cookie 可能被别的任务线程回写过（yt-dlp 轮换），所以每次下载前
        重新比对一次快照；``force=True`` 用于重试前强制重建。
        """
        cookie = CookieConfigManager().get("youtube") or ""
        if not cookie:
            self._cleanup_cookie_file()
            return None

        unchanged = (
            not force
            and self._cookiefile
            and os.path.exists(self._cookiefile)
            and cookie == self._cookie_snapshot
        )
        if unchanged:
            return self._cookiefile

        self._cleanup_cookie_file()
        fd, path = tempfile.mkstemp(prefix="yt_cookie_", suffix=".txt")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(_to_netscape(cookie))
        self._cookiefile = path
        self._cookie_snapshot = cookie
        logger.info(f"已生成 YouTube Cookie 文件（{len(_split_cookie_header(cookie))} 条）")
        return path

    def _cleanup_cookie_file(self) -> None:
        if self._cookiefile:
            try:
                os.unlink(self._cookiefile)
            except OSError:
                pass
        self._cookiefile = None
        self._cookie_snapshot = None

    def _persist_rotated_cookies(self) -> None:
        """把 yt-dlp 轮换后的 Cookie 写回 config/downloader.json。

        Google 会定期轮换 `__Secure-1PSIDTS` 之类的会话 Cookie。以前每次都用配置里
        的旧字符串重建临时文件，轮换一次之后保存的 Cookie 就永久失效，后续所有请求
        都会被要求「Sign in to confirm you're not a bot」。这里把 yt-dlp 回写的文件
        同步回配置，下次任务就能用上新值。
        """
        if not self._cookiefile or not os.path.exists(self._cookiefile):
            return
        rotated = _read_netscape(self._cookiefile)
        if not rotated:
            return
        try:
            manager = CookieConfigManager()
            current = _split_cookie_header(manager.get("youtube") or "")
            # 以 yt-dlp 回写的值为准，但配置里已有、本次没被回写的条目要保留：
            # yt-dlp 的 cookie jar 可能按策略丢弃个别条目，误删登录凭据会让整个
            # 账号态直接失效。
            merged: dict = dict(current)
            merged.update(rotated)
            if merged == dict(current):
                return
            manager.set(
                "youtube", "; ".join(f"{name}={value}" for name, value in merged.items())
            )
            logger.info(f"已把 yt-dlp 轮换后的 YouTube Cookie 写回配置（{len(merged)} 条）")
        except Exception as exc:  # 回写失败不能影响主流程
            logger.warning(f"回写 YouTube Cookie 失败（忽略）：{exc}")

    # ---------------- 下载执行 ----------------
    def _extract_with_retry(self, ydl_opts: dict, video_url: str, download: bool):
        """执行 yt-dlp 提取；遇到反爬/429 时按指数退避重试。

        重试前会把轮换后的 Cookie 落盘并重建临时文件，尽量让下一次请求带上新凭据。
        """
        attempts = max(1, int(os.getenv("YOUTUBE_RETRY_ATTEMPTS", "3")))
        base_delay = max(0.0, float(os.getenv("YOUTUBE_RETRY_BASE_DELAY", "8")))

        last_exc: Optional[BaseException] = None
        # 重试时可能换成重建后的 Cookie 文件，但基础选项（含 YDL_RETRY_OPTS）保持不变
        attempt_opts = ydl_opts
        for attempt in range(1, attempts + 1):
            try:
                with yt_dlp.YoutubeDL(attempt_opts) as ydl:
                    return ydl.extract_info(video_url, download=download)
            except Exception as exc:
                last_exc = exc
                if not _is_anti_bot_error(exc):
                    raise
                if attempt >= attempts:
                    break
                # 指数退避 + 抖动，避免同一时刻的并发任务再次挤在一起触发限流
                delay = base_delay * (2 ** (attempt - 1)) + random.uniform(0, 2)
                logger.warning(
                    f"YouTube 反爬拦截（第 {attempt}/{attempts} 次），{delay:.1f}s 后重试："
                    f"{str(exc).splitlines()[0][:160]}"
                )
                time.sleep(delay)
                self._persist_rotated_cookies()
                self._ensure_cookie_file(force=True)
                if self._cookiefile:
                    attempt_opts = {**ydl_opts, "cookiefile": self._cookiefile}

        raise YouTubeAccessBlockedError(
            f"{_YOUTUBE_BLOCKED_HINT}\n原始错误：{last_exc}"
        ) from last_exc

    def _run_ydl(self, ydl_opts: dict, video_url: str, download: bool):
        """跑一次 yt-dlp，并负责 Cookie 文件的创建 / 回收 / 轮换回写。"""
        _apply_proxy(ydl_opts)
        self._ensure_cookie_file()
        if self._cookiefile:
            ydl_opts["cookiefile"] = self._cookiefile
        try:
            return self._extract_with_retry(ydl_opts, video_url, download)
        finally:
            self._persist_rotated_cookies()
            self._cleanup_cookie_file()

    def download(
        self,
        video_url: str,
        output_dir: Union[str, None] = None,
        quality: DownloadQuality = "fast",
        need_video: Optional[bool] = False,
        skip_download: bool = False,
    ) -> AudioDownloadResult:
        if output_dir is None:
            output_dir = get_data_dir()
        if not output_dir:
            output_dir = self.cache_data
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, "%(id)s.%(ext)s")

        ydl_opts = {
            **YDL_RETRY_OPTS,
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': output_path,
            'noplaylist': True,
            'quiet': False,
            'js_runtimes': {'node': {}},
        }

        if skip_download:
            ydl_opts['skip_download'] = True
            # 只取元信息时并不需要媒体流。yt-dlp 版本落后于 YouTube player 时，
            # nsig 解析失败会导致所有音视频格式被丢弃，此时格式选择会抛
            # "Requested format is not available"，把一个已经拿到字幕的任务带崩。
            ydl_opts['ignore_no_formats_error'] = True

        info = self._run_ydl(ydl_opts, video_url, download=not skip_download)
        video_id = info.get("id")
        title = info.get("title")
        duration = info.get("duration", 0)
        cover_url = info.get("thumbnail")
        # skip_download 时 yt-dlp 返回 ext=None，默认值不会生效，避免拼出 "xxx.None"
        ext = info.get("ext") or "m4a"
        audio_path = os.path.join(output_dir, f"{video_id}.{ext}")

        return AudioDownloadResult(
            file_path=audio_path,
            title=title,
            duration=duration,
            cover_url=cover_url,
            platform="youtube",
            video_id=video_id,
            raw_info={'tags': info.get('tags')},
            video_path=None,
        )

    def download_video(
        self,
        video_url: str,
        output_dir: Union[str, None] = None,
    ) -> str:
        """
        下载视频，返回视频文件路径
        """
        if output_dir is None:
            output_dir = get_data_dir()
        video_id = extract_video_id(video_url, "youtube")
        video_path = os.path.join(output_dir, f"{video_id}.mp4")
        if os.path.exists(video_path):
            return video_path
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "%(id)s.%(ext)s")

        ydl_opts = {
            **YDL_RETRY_OPTS,
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': output_path,
            'noplaylist': True,
            'quiet': False,
            'js_runtimes': {'node': {}},
            'merge_output_format': 'mp4',  # 确保合并成 mp4
        }

        info = self._run_ydl(ydl_opts, video_url, download=True)
        video_id = info.get("id")
        video_path = os.path.join(output_dir, f"{video_id}.mp4")

        if not os.path.exists(video_path):
            raise FileNotFoundError(f"视频文件未找到: {video_path}")

        return video_path

    def download_subtitles(self, video_url: str, output_dir: str = None,
                           langs: List[str] = None) -> Optional[TranscriptResult]:
        """
        通过 YouTube InnerTube API 直接获取字幕（优先人工字幕，其次自动生成）。
        比 yt_dlp 方式更轻量，无需写临时文件到磁盘。

        :param video_url: 视频链接
        :param output_dir: 未使用（保留接口兼容）
        :param langs: 优先语言列表
        :return: TranscriptResult 或 None
        """
        if langs is None:
            langs = ['zh-Hans', 'zh', 'zh-CN', 'zh-TW', 'en', 'en-US', 'ja']

        video_id = extract_video_id(video_url, "youtube")
        fetcher = YouTubeSubtitleFetcher()
        print(
            f"尝试获取字幕，video_id={video_id}, langs={langs}"
        )
        return fetcher.fetch_subtitles(video_id, langs)
