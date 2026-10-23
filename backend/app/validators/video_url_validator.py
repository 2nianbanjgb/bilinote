from pydantic import AnyUrl, validator, BaseModel, field_validator, model_validator
import re
from urllib.parse import urlparse

from app.utils.url_parser import normalize_video_url

SUPPORTED_PLATFORMS = {
    "bilibili": r"(https?://)?(www\.)?bilibili\.com/video/[a-zA-Z0-9]+",
    "youtube": r"(https?://)?(www\.)?(youtube\.com/(watch\?v=|shorts/)|youtu\.be/)[\w\-]+",
    "douyin": r"(v\.douyin\.com/[\w\-]+|(www\.)?douyin\.com/video/\d+|iesdouyin\.com/share/video/\d+)",
    "kuaishou": r"(v\.kuaishou\.com/[\w\-]+|(www\.)?kuaishou\.com/(short-video|f)/[\w\-]+)"
}


def is_supported_video_url(url: str) -> bool:
    parsed = urlparse(url)

    # 检查是否为Bilibili的短链接
    if parsed.netloc == "b23.tv":
        return True

    for name, pattern in SUPPORTED_PLATFORMS.items():
        if re.search(pattern, url):
            return True
    return False


class VideoRequest(BaseModel):
    url: AnyUrl
    platform: str

    @model_validator(mode="before")
    @classmethod
    def normalize_url(cls, data):
        if isinstance(data, dict) and data.get("platform") == "bilibili" and data.get("url"):
            data["url"] = normalize_video_url(str(data["url"]))
        return data

    @field_validator("url")
    def validate_video_url(cls, v):
        if not is_supported_video_url(str(v)):
            raise ValueError("只支持单个视频链接：抖音请用 https://www.douyin.com/video/数字 或 v.douyin.com 分享短链，不支持主页/收藏夹/直播")
        return v
