import logging
import re
import feedparser

log = logging.getLogger(__name__)

FEEDS = {
    "left":   "https://feeds.npr.org/1001/rss.xml",
    "center": "https://feeds.reuters.com/reuters/topNews",
    "right":  "https://moxie.foxnews.com/google-publisher/latest.xml",
}
FEED_LABELS = {
    "left":   "NPR",
    "center": "Reuters",
    "right":  "Fox News",
}


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).strip()


def fetch_headlines(label: str, url: str, max_items: int = 5) -> list[dict]:
    log.info("Fetching %s feed", label)
    try:
        feed = feedparser.parse(url)
        if feed.bozo:
            log.warning("%s feed has XML issues — continuing with partial data", label)
        if not feed.entries:
            log.warning("%s feed returned no entries", label)
            return []
        headlines = []
        for entry in feed.entries[:max_items]:
            title   = entry.get("title", "").strip()
            summary = _strip_html(entry.get("summary", entry.get("description", "")).strip())
            if title:
                headlines.append({"title": title, "summary": summary[:300]})
        log.info("%s: fetched %d headlines", label, len(headlines))
        return headlines
    except Exception as exc:
        log.error("Failed to fetch %s feed: %s", label, exc, exc_info=True)
        return []


def fetch_all_headlines(max_per_source: int = 5) -> dict[str, list[dict]]:
    return {
        bias: fetch_headlines(FEED_LABELS[bias], url, max_per_source)
        for bias, url in FEEDS.items()
    }
