"""YouTube 专用代理与全局代理的优先级。

YouTube 对机房 IP 的风控远严于 B 站 / 抖音，所以允许单独配置一条线路：
  - 配了 youtube_url → YouTube 走它（即使全局代理没开）；
  - 没配 youtube_url → 回落全局代理（保持旧行为）；
  - 其它平台只读全局代理，永远读不到 youtube_url。
"""
import importlib.util
import os
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "app" / "services" / "proxy_config_manager.py"
spec = importlib.util.spec_from_file_location("proxy_config_manager_youtube", MODULE_PATH)
if spec is None or spec.loader is None:
    raise ImportError("proxy_config_manager module spec not found")
pcm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pcm)
ProxyConfigManager = pcm.ProxyConfigManager

PROXY_ENV_KEYS = (
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "all_proxy",
)


class TestYoutubeProxy(unittest.TestCase):
    def setUp(self):
        self._saved = {k: os.environ.get(k) for k in PROXY_ENV_KEYS}
        for k in PROXY_ENV_KEYS:
            os.environ.pop(k, None)
        self._tmp = tempfile.TemporaryDirectory()
        self.cfg_path = os.path.join(self._tmp.name, "proxy.json")

    def tearDown(self):
        for k, v in self._saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        self._tmp.cleanup()

    def test_youtube_url_overrides_global(self):
        mgr = ProxyConfigManager(filepath=self.cfg_path)
        mgr.update_config(
            enabled=True,
            url="http://127.0.0.1:7890",
            youtube_url="http://10.1.2.3:1080",
        )
        self.assertEqual(mgr.get_proxy_url(), "http://127.0.0.1:7890")
        self.assertEqual(mgr.get_youtube_proxy_url(), "http://10.1.2.3:1080")

    def test_falls_back_to_global_when_youtube_url_is_empty(self):
        mgr = ProxyConfigManager(filepath=self.cfg_path)
        mgr.update_config(enabled=True, url="http://127.0.0.1:7890", youtube_url="")
        self.assertEqual(mgr.get_youtube_proxy_url(), "http://127.0.0.1:7890")

    def test_youtube_proxy_works_even_when_global_is_disabled(self):
        mgr = ProxyConfigManager(filepath=self.cfg_path)
        mgr.update_config(enabled=False, url="", youtube_url="socks5://127.0.0.1:1080")
        self.assertIsNone(mgr.get_proxy_url())
        self.assertEqual(mgr.get_youtube_proxy_url(), "socks5://127.0.0.1:1080")

    def test_no_configuration_returns_none(self):
        mgr = ProxyConfigManager(filepath=self.cfg_path)
        self.assertIsNone(mgr.get_youtube_proxy_url())

    def test_env_fallback_applies_to_youtube_too(self):
        os.environ["HTTPS_PROXY"] = "http://10.0.0.1:1080"
        mgr = ProxyConfigManager(filepath=self.cfg_path)
        self.assertEqual(mgr.get_youtube_proxy_url(), "http://10.0.0.1:1080")

    def test_apply_to_env_ignores_youtube_url(self):
        """环境变量是进程级的，不能只给 YouTube 用，所以只导出全局代理。"""
        mgr = ProxyConfigManager(filepath=self.cfg_path)
        mgr.update_config(enabled=False, url="", youtube_url="http://10.1.2.3:1080")
        self.assertIsNone(mgr.apply_to_env())
        for k in PROXY_ENV_KEYS:
            self.assertIsNone(os.environ.get(k), k)


if __name__ == "__main__":
    unittest.main()
