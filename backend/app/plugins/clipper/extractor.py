"""
网页正文抽取
抓取 HTML → 清洗噪声标签 → 定位正文容器 → 转成 Markdown 风格纯文本

说明：环境未安装 trafilatura / readability，这里基于 BeautifulSoup 实现轻量抽取，
      对技术博客、公众号文章、资讯页等静态页面效果良好；JS 渲染页会抽取失败并明确报错。
"""
import hashlib
import re
from datetime import datetime
from typing import Dict, List
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests
from bs4 import BeautifulSoup, Tag

from app.core.exceptions import BusinessException

# 请求头（部分站点会拒绝空 UA）
REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}

# 抓取超时（秒）
FETCH_TIMEOUT = 20

# 需要整体删除的噪声标签
NOISE_TAGS = [
    "script", "style", "noscript", "iframe", "svg", "canvas", "form",
    "nav", "header", "footer", "aside",
]

# 需要删除的噪声 class / id 关键词
NOISE_PATTERN = re.compile(
    r"(comment|share|sidebar|footer|header|nav|menu|advert|ads?\b|banner|"
    r"related|recommend|subscribe|newsletter|breadcrumb|copyright|toolbar|popup)",
    re.I,
)

# 按顺序输出的块级标签
BLOCK_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "blockquote", "pre", "figcaption", "td"]

# 追踪参数，规范化时剔除
TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "spm", "from", "share_token", "scene", "srcid", "clicktime", "sessionid",
}


def normalize_url(url: str) -> str:
    """规范化 URL：补全协议、剔除 fragment 与追踪参数"""
    url = (url or "").strip()
    if not url:
        raise BusinessException(message="链接不能为空", code=3001)

    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url

    parsed = urlparse(url)
    if not parsed.netloc:
        raise BusinessException(message="链接格式不正确", code=3002)

    # 剔除追踪参数，保留业务参数
    query_pairs = [
        (k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if k.lower() not in TRACKING_PARAMS and not k.lower().startswith("utm_")
    ]
    # 路径去掉末尾多余的 /
    path = parsed.path.rstrip("/") or "/"

    return urlunparse(
        (parsed.scheme.lower(), parsed.netloc.lower(), path, "", urlencode(query_pairs), "")
    )


def url_fingerprint(normalized_url: str) -> str:
    """生成链接指纹（SHA256）"""
    return hashlib.sha256(normalized_url.encode("utf-8")).hexdigest()


def fetch_html(url: str) -> str:
    """抓取网页 HTML"""
    try:
        resp = requests.get(url, headers=REQUEST_HEADERS, timeout=FETCH_TIMEOUT)
    except requests.exceptions.SSLError:
        # 部分站点证书异常，降级重试一次
        try:
            resp = requests.get(url, headers=REQUEST_HEADERS, timeout=FETCH_TIMEOUT, verify=False)
        except requests.RequestException as e:
            raise BusinessException(message=f"网页抓取失败: {e}", code=3003)
    except requests.RequestException as e:
        raise BusinessException(message=f"网页抓取失败: {e}", code=3003)

    if resp.status_code >= 400:
        raise BusinessException(
            message=f"网页返回错误状态码 {resp.status_code}，可能不允许抓取",
            code=3004,
        )

    # 编码修正：优先用响应头声明，否则尝试 utf-8 / gbk
    if not resp.encoding or resp.encoding.lower() == "iso-8859-1":
        raw = resp.content
        for enc in ("utf-8", "gbk", "gb18030"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("utf-8", errors="ignore")

    resp.encoding = resp.apparent_encoding or resp.encoding
    return resp.text


def _pick_container(soup: BeautifulSoup) -> Tag:
    """定位正文容器：article > main > 文本量最大的 div > body"""
    for tag_name in ("article", "main"):
        node = soup.find(tag_name)
        if node and len(node.get_text(strip=True)) > 200:
            return node

    # 按文本长度打分选择 div / section
    best_node = None
    best_len = 0
    for node in soup.find_all(["div", "section"]):
        text_len = len(node.get_text(strip=True))
        # 嵌套容器会重复计数，用段落数量做加权，避免选到最外层空壳
        p_count = len(node.find_all("p"))
        score = text_len + p_count * 50
        if score > best_len:
            best_len = score
            best_node = node

    if best_node is not None and best_len > 200:
        return best_node

    return soup.body or soup


def _clean(soup: BeautifulSoup) -> None:
    """移除噪声标签与噪声区块"""
    for tag in soup(NOISE_TAGS):
        tag.decompose()

    for node in soup.find_all(True):
        if not isinstance(node, Tag) or node.attrs is None:
            continue
        marker = " ".join(
            filter(None, [node.get("class") and " ".join(node.get("class")), node.get("id") or ""])
        )
        if marker and NOISE_PATTERN.search(marker):
            node.decompose()


def _meta_content(soup: BeautifulSoup, *keys: str) -> str:
    """读取 meta 标签内容，支持 property / name 两种写法"""
    for key in keys:
        node = soup.find("meta", attrs={"property": key}) or soup.find("meta", attrs={"name": key})
        if node and node.get("content"):
            return node["content"].strip()
    return ""


def _to_markdown(container: Tag) -> str:
    """把正文容器转成 Markdown 风格的纯文本"""
    lines: List[str] = []
    seen = set()

    for node in container.find_all(BLOCK_TAGS):
        name = node.name

        # 跳过嵌套在已输出块里的重复内容
        if name == "p" and node.find_parent("li"):
            continue
        if name == "p" and node.find_parent("blockquote"):
            continue
        if name in {"h1", "h2", "h3", "h4", "h5", "h6"} and node.find_parent("blockquote"):
            continue

        text = node.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        if not text or len(text) < 2:
            continue

        # 简单去重：完全相同的相邻块只保留一次
        key = (name, text)
        if key in seen:
            continue
        seen.add(key)

        if name == "pre":
            lines.append("```\n" + node.get_text("\n", strip=True) + "\n```")
        elif name.startswith("h") and len(name) == 2 and name[1].isdigit():
            level = int(name[1])
            lines.append("#" * level + " " + text)
        elif name == "li":
            lines.append("- " + text)
        elif name == "blockquote":
            lines.append("> " + text)
        elif name == "td":
            continue
        else:
            # 段落过长时按中文句号切段，便于后续分块
            lines.append(text)

    if not lines:
        # 兜底：整容器纯文本按段落切
        raw = container.get_text("\n", strip=True)
        lines = [ln.strip() for ln in raw.split("\n") if len(ln.strip()) >= 2]

    return "\n\n".join(lines)


def extract_article(html: str, url: str) -> Dict[str, str]:
    """
    从 HTML 中抽取文章信息

    Returns:
        {title, site_name, author, content_md, summary}
    """
    soup = BeautifulSoup(html, "html.parser")
    _clean(soup)

    parsed = urlparse(url)
    site_name = _meta_content(soup, "og:site_name") or parsed.netloc
    author = _meta_content(soup, "author", "article:author", "og:article:author")

    # 标题优先取 og:title，其次 <title>，最后第一个 h1
    title = _meta_content(soup, "og:title")
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        h1 = soup.find("h1")
        title = h1.get_text(strip=True) if h1 else ""
    # 去掉常见的站点后缀
    title = re.sub(r"\s*[-_|｜]\s*" + re.escape(site_name) + r"\s*$", "", title).strip()
    title = title[:200] or "未命名剪藏"

    container = _pick_container(soup)
    content_md = _to_markdown(container)

    if len(content_md) < 100:
        raise BusinessException(
            message="未能抽取到有效正文，可能是动态渲染页面或存在反爬限制，可手动复制正文入库",
            code=3005,
        )

    plain = re.sub(r"\s+", " ", re.sub(r"^#+\s*", "", content_md, flags=re.M)).strip()
    summary = plain[:200]

    return {
        "title": title,
        "site_name": site_name[:100],
        "author": author[:100],
        "content_md": content_md,
        "summary": summary,
    }


def build_markdown(article: Dict[str, str], url: str, tags: List[str], category: str) -> str:
    """组装带元信息的 Markdown 正文"""
    tag_line = "、".join(tags) if tags else "无"
    header = [
        "---",
        f"source: {url}",
        f"title: {article['title']}",
        f"site: {article['site_name']}",
        f"author: {article.get('author') or ''}",
        f"category: {category or ''}",
        f"tags: {tag_line}",
        f"clipped_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "---",
        "",
        f"# {article['title']}",
        "",
        f"> 来源：{url}",
        "",
    ]
    return "\n".join(header) + article["content_md"] + "\n"
