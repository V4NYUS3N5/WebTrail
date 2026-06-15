"""
URL 解析工具 - 域名提取、分类等。
"""
from __future__ import annotations


# ---- 域名提取 ----

def extract_domain(url_or_host: str) -> str:
    """从 URL 或 host 字符串提取纯域名。"""
    if not url_or_host:
        return ""
    s = url_or_host.strip().lstrip(".")  # 去掉 cookie 域名的前导点
    for prefix in ("https://", "http://"):
        if s.startswith(prefix):
            s = s[len(prefix):]
    return s.split("/")[0].split(":")[0].strip()


def extract_domain_from_record(data: dict) -> str:
    """从 ArtifactRecord.data 中提取域名（兼容多种键名）。"""
    raw = data.get("url", "") or data.get("host", "") or data.get("host_key", "")
    return extract_domain(raw)


# ---- URL 分类规则 ----

URL_CATEGORIES: dict[str, list[str]] = {
    "社交媒体": ["facebook.com", "twitter.com", "x.com", "instagram.com", "weibo.com",
               "tiktok.com", "reddit.com", "linkedin.com", "zhihu.com"],
    "搜索引擎": ["google.com/search", "bing.com/search", "baidu.com/s",
               "duckduckgo.com", "sogou.com"],
    "视频": ["youtube.com", "bilibili.com", "vimeo.com", "dailymotion.com",
            "netflix.com", "twitch.tv", "douyin.com", "iqiyi.com"],
    "购物": ["amazon.com", "taobao.com", "jd.com", "ebay.com", "aliexpress.com",
            "pinduoduo.com", "shopify.com"],
    "邮箱": ["mail.google.com", "outlook.live.com", "mail.yahoo.com",
            "mail.163.com", "mail.qq.com", "proton.me"],
    "技术开发": ["github.com", "gitlab.com", "stackoverflow.com", "npmjs.com",
               "pypi.org", "docker.com", "dev.to"],
    "新闻": ["cnn.com", "bbc.com", "reuters.com", "news.qq.com",
            "sina.com.cn", "theguardian.com"],
    "云存储": ["drive.google.com", "dropbox.com", "onedrive.live.com",
             "pan.baidu.com"],
}


def classify_url(url: str) -> str:
    """根据 URL 关键词返回类别名称，未匹配返回 '其他'。"""
    url_l = url.lower()
    for category, keywords in URL_CATEGORIES.items():
        if any(k in url_l for k in keywords):
            return category
    return "其他"
