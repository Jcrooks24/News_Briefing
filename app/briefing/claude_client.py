import logging
from datetime import datetime
import anthropic

log = logging.getLogger(__name__)

_NEWS_SYSTEM = """\
You are a calm, warm morning radio host writing a spoken-word news briefing script.
Your tone is clear, conversational, and unhurried — like a trusted friend reading \
the news over coffee.  You never editorialize or take sides; you simply report what \
each outlet is saying and note differences in framing.

Rules:
- Write in plain spoken English — no bullet points, no headers, no markdown.
- Total length should be 450–600 words (about 3–4 minutes when read aloud).
- Begin with a brief greeting that addresses the listener by name and mentions today's date.
- Cover the top stories from each of the three sources.
- After presenting all stories, briefly compare how the left-leaning, center, \
and right-leaning outlets are framing the day's news (1–2 sentences).
- End with a short, warm send-off.
"""

_WILDCARD_SYSTEM = """\
You are a warm, curious, and witty morning radio host who occasionally ditches \
the news to talk about something completely different — just for the fun of it.

Rules:
- Write in plain spoken English — no bullet points, no headers, no markdown.
- Total length should be 450–600 words (about 3–4 minutes when read aloud).
- Begin with a greeting that addresses the listener by name, mentions today's date, \
and cheekily explains that today you're skipping the news entirely.
- Spend the rest of the time diving enthusiastically into the given topic. \
Share surprising facts, tell a short story or two, and make it genuinely \
entertaining — like a mini podcast segment.
- End with a warm, upbeat send-off.
"""

FEED_LABELS = {"left": "NPR", "center": "Reuters", "right": "Fox News"}


def _stream(system: str, user_message: str, api_key: str) -> str:
    client = anthropic.Anthropic(api_key=api_key)
    parts: list[str] = []
    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=1024,
        thinking={"type": "adaptive"},
        system=system,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        for chunk in stream.text_stream:
            parts.append(chunk)
        final = stream.get_final_message()
    script = "".join(parts).strip()
    log.info("Claude returned %d words (stop_reason=%s)", len(script.split()), final.stop_reason)
    if not script:
        raise ValueError("Claude returned an empty script")
    return script


def generate_news_script(
    headlines: dict[str, list[dict]],
    user_name: str,
    api_key: str,
) -> str:
    today = datetime.now().strftime("%A, %B %d, %Y")
    lines = [f"Today is {today}. The listener's name is {user_name}. Here are the headlines:\n"]
    for bias, label in FEED_LABELS.items():
        items = headlines.get(bias, [])
        if items:
            lines.append(f"## {label} ({bias.upper()}-leaning)\n")
            for i, item in enumerate(items, 1):
                lines.append(f"{i}. {item['title']}")
                if item["summary"]:
                    lines.append(f"   {item['summary']}")
            lines.append("")
        else:
            lines.append(f"## {label} — no headlines available today\n")
    lines.append("Please write the morning briefing script now. Plain prose only, 450–600 words, spoken-word style.")
    return _stream(_NEWS_SYSTEM, "\n".join(lines), api_key)


def generate_wildcard_script(
    topic: str,
    user_name: str,
    api_key: str,
) -> str:
    today = datetime.now().strftime("%A, %B %d, %Y")
    user_message = (
        f"Today is {today}. The listener's name is {user_name}.\n\n"
        f"Today's topic: {topic}\n\n"
        "Please write the morning segment now. Plain prose only, 450–600 words, spoken-word style."
    )
    return _stream(_WILDCARD_SYSTEM, user_message, api_key)
