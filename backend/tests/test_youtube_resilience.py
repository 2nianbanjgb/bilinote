"""YouTube 下载健壮性：Cookie 轮换回写、反爬退避、专用代理。

背景：YouTube 会轮换 __Secure-1PSIDTS 之类的会话 Cookie，同时把「短时间批量拉全片」
的出口 IP 判定为机器人。旧实现每次都用配置里的静态 Cookie 字符串重建临时文件、
轮换结果直接丢弃，于是 Cookie 失效一次后所有任务都会卡在
\"Sign in to confirm you're not a bot\"，且没有任何退避与可读的报错。
"""
import importlib.util
import os
import pathlib
import sys
import tempfile
import types
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "app" / "downloaders" / "youtube_downloader.py"

INITIAL_COOKIE = "SID=old; __Secure-1PSIDTS=1100"
BOT_ERROR = (
    "ERROR: [youtube] abc: Sign in to confirm you're not a bot. "
    "Use --cookies-from-browser or --cookies for the authentication."
)


def _stub(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module
    return module


class _CookieStore:
    data = {}
    writes = 0

    @classmethod
    def reset(cls, cookie=INITIAL_COOKIE):
        cls.data = {"youtube": cookie} if cookie is not None else {}
        cls.writes = 0


class _CookieManager:
    def __init__(self, *args, **kwargs):
        pass

    def get(self, platform):
        return _CookieStore.data.get(platform)

    def set(self, platform, cookie):
        _CookieStore.data[platform] = cookie
        _CookieStore.writes += 1


class _ProxyManager:
    youtube_proxy = None

    def get_youtube_proxy_url(self):
        return _ProxyManager.youtube_proxy

    def get_proxy_url(self):
        return None


class _Downloader:
    def __init__(self):
        self.cache_data = "/tmp"


class _AudioDownloadResult:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


def _load_module():
    _stub("app")
    _stub("app.downloaders")
    _stub("app.models")
    _stub("app.services")
    _stub("app.utils")
    _stub(
        "app.downloaders.base",
        Downloader=_Downloader,
        DownloadQuality=str,
        YDL_RETRY_OPTS={"retries": 3, "fragment_retries": 3, "socket_timeout": 30},
    )
    _stub("app.downloaders.youtube_subtitle", YouTubeSubtitleFetcher=object)
    _stub("app.models.notes_model", AudioDownloadResult=_AudioDownloadResult)
    _stub("app.models.transcriber_model", TranscriptResult=object)
    _stub("app.services.cookie_manager", CookieConfigManager=_CookieManager)
    _stub("app.services.proxy_config_manager", ProxyConfigManager=_ProxyManager)
    _stub("app.utils.path_helper", get_data_dir=lambda: "/tmp")
    _stub("app.utils.url_parser", extract_video_id=lambda url, platform: "vid")

    spec = importlib.util.spec_from_file_location(
        "youtube_downloader_resilience", MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise ImportError("youtube_downloader module spec not found")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _info():
    return {
        "id": "vid",
        "title": "example",
        "duration": 1,
        "thumbnail": None,
        "ext": "m4a",
        "tags": [],
    }


def _write_cookie(path, pairs, httponly=()):
    lines = ["# Netscape HTTP Cookie File", ""]
    for name, value in pairs:
        domain = ".youtube.com"
        if name in httponly:
            domain = "#HttpOnly_" + domain
        lines.append(
            "\t".join([domain, "TRUE", "/", "TRUE", "2147483647", name, value])
        )
    pathlib.Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


class _FakeYoutubeDL:
    """模拟 yt-dlp：可记录 opts、按需回写 Cookie、按需抛错。"""

    captured_opts = None
    behavior = None

    def __init__(self, opts):
        type(self).captured_opts = dict(opts)

    def __enter__(self):
        return self

    def __exit__(self, *exc_info):
        return False

    def extract_info(self, url, download=True):
        return type(self).behavior(type(self).captured_opts, url, download)


class YoutubeResilienceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.module = _load_module()
        except Exception as exc:  # pragma: no cover - env without yt-dlp
            raise unittest.SkipTest(f"youtube_downloader not importable: {exc}")

    def setUp(self):
        _CookieStore.reset()
        _ProxyManager.youtube_proxy = None
        _FakeYoutubeDL.behavior = None
        self._real_ydl = self.module.yt_dlp.YoutubeDL
        self.module.yt_dlp.YoutubeDL = _FakeYoutubeDL
        self._env = {}
        for key in ("YOUTUBE_RETRY_ATTEMPTS", "YOUTUBE_RETRY_BASE_DELAY"):
            self._env[key] = os.environ.pop(key, None)

    def tearDown(self):
        self.module.yt_dlp.YoutubeDL = self._real_ydl
        for key, value in self._env.items():
            os.environ.pop(key, None)
            if value is not None:
                os.environ[key] = value

    def test_rotated_cookie_is_written_back_to_config(self):
        """yt-dlp 轮换后的 Cookie 必须持久化，否则失效一次就永久失效。"""

        def behavior(opts, url, download):
            _write_cookie(
                opts["cookiefile"],
                [("SID", "old"), ("__Secure-1PSIDTS", "2200"), ("LOGIN_INFO", "x")],
                httponly={"SID", "LOGIN_INFO"},
            )
            return _info()

        _FakeYoutubeDL.behavior = behavior
        self.module.YoutubeDownloader().download("https://youtu.be/x", "/tmp")

        saved = _CookieStore.data["youtube"]
        # HttpOnly 的登录凭据（SID / LOGIN_INFO）不能被当成注释行丢掉
        self.assertIn("SID=old", saved)
        self.assertIn("__Secure-1PSIDTS=2200", saved)
        self.assertIn("LOGIN_INFO=x", saved)
        self.assertEqual(_CookieStore.writes, 1)

    def test_cookie_dropped_by_yt_dlp_is_kept_from_config(self):
        """yt-dlp 的 jar 可能丢弃个别条目，回写时不能把配置里的凭据洗没。"""
        _CookieStore.reset("SID=old; HSID=keep; __Secure-1PSIDTS=1100")

        def behavior(opts, url, download):
            _write_cookie(
                opts["cookiefile"], [("SID", "old"), ("__Secure-1PSIDTS", "2200")]
            )
            return _info()

        _FakeYoutubeDL.behavior = behavior
        self.module.YoutubeDownloader().download("https://youtu.be/x", "/tmp")

        saved = _CookieStore.data["youtube"]
        self.assertIn("HSID=keep", saved)
        self.assertIn("__Secure-1PSIDTS=2200", saved)

    def test_unchanged_cookie_is_not_rewritten(self):
        def behavior(opts, url, download):
            _write_cookie(
                opts["cookiefile"], [("SID", "old"), ("__Secure-1PSIDTS", "1100")]
            )
            return _info()

        _FakeYoutubeDL.behavior = behavior
        self.module.YoutubeDownloader().download("https://youtu.be/x", "/tmp")
        self.assertEqual(_CookieStore.writes, 0)

    def test_antibot_error_retries_with_backoff_then_raises_readable_error(self):
        os.environ["YOUTUBE_RETRY_ATTEMPTS"] = "3"
        os.environ["YOUTUBE_RETRY_BASE_DELAY"] = "0"
        calls = []

        def behavior(opts, url, download):
            calls.append(1)
            raise RuntimeError(BOT_ERROR)

        _FakeYoutubeDL.behavior = behavior
        with mock.patch.object(self.module.time, "sleep") as sleep:
            with self.assertRaises(self.module.YouTubeAccessBlockedError) as ctx:
                self.module.YoutubeDownloader().download("https://youtu.be/x", "/tmp")

        self.assertEqual(len(calls), 3)
        self.assertEqual(sleep.call_count, 2)
        message = str(ctx.exception)
        self.assertIn("YouTube 拒绝了本次下载", message)
        self.assertIn("重新导出 YouTube Cookie", message)

    def test_unrelated_error_is_not_retried(self):
        calls = []

        def behavior(opts, url, download):
            calls.append(1)
            raise ValueError("boom")

        _FakeYoutubeDL.behavior = behavior
        with self.assertRaises(ValueError):
            self.module.YoutubeDownloader().download("https://youtu.be/x", "/tmp")
        self.assertEqual(len(calls), 1)

    def test_youtube_uses_dedicated_proxy(self):
        _ProxyManager.youtube_proxy = "http://127.0.0.1:7891"
        _FakeYoutubeDL.behavior = lambda opts, url, download: _info()
        self.module.YoutubeDownloader().download(
            "https://youtu.be/x", "/tmp", skip_download=True
        )
        self.assertEqual(
            _FakeYoutubeDL.captured_opts.get("proxy"), "http://127.0.0.1:7891"
        )

    def test_no_proxy_configured_means_direct_connection(self):
        _FakeYoutubeDL.behavior = lambda opts, url, download: _info()
        self.module.YoutubeDownloader().download(
            "https://youtu.be/x", "/tmp", skip_download=True
        )
        self.assertNotIn("proxy", _FakeYoutubeDL.captured_opts)


class CookieRoundTripTest(unittest.TestCase):
    """Cookie 头 <-> Netscape 文件的转换必须是可逆的。"""

    @classmethod
    def setUpClass(cls):
        try:
            cls.module = _load_module()
        except Exception as exc:  # pragma: no cover
            raise unittest.SkipTest(f"youtube_downloader not importable: {exc}")

    def test_header_round_trip(self):
        cookie = "SID=a=b; __Secure-1PSIDTS=123; HSID=zzz"
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cookies.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.module._to_netscape(cookie))
            pairs = self.module._read_netscape(path)
        self.assertEqual(pairs, [("SID", "a=b"), ("__Secure-1PSIDTS", "123"), ("HSID", "zzz")])

    def test_expired_entries_are_dropped(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cookies.txt")
            pathlib.Path(path).write_text(
                "# Netscape HTTP Cookie File\n"
                ".youtube.com\tTRUE\t/\tTRUE\t1000000000\tOLD\t1\n"
                ".youtube.com\tTRUE\t/\tTRUE\t2147483647\tNEW\t2\n",
                encoding="utf-8",
            )
            pairs = self.module._read_netscape(path)
        self.assertEqual(pairs, [("NEW", "2")])

    def test_httponly_entries_are_not_treated_as_comments(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "cookies.txt")
            pathlib.Path(path).write_text(
                "# Netscape HTTP Cookie File\n"
                "#HttpOnly_.youtube.com\tTRUE\t/\tTRUE\t2147483647\tSID\tsecret\n"
                "# a real comment line\n"
                ".youtube.com\tTRUE\t/\tTRUE\t2147483647\tPREF\tlang\n",
                encoding="utf-8",
            )
            pairs = self.module._read_netscape(path)
        self.assertEqual(pairs, [("SID", "secret"), ("PREF", "lang")])


if __name__ == "__main__":
    unittest.main()
