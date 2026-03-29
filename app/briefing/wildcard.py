import random
from datetime import date

WILDCARD_TOPICS = [
    "the surprisingly bizarre history of breakfast cereal",
    "how deep-sea creatures survive crushing pressure and total darkness",
    "the strange and convoluted history of daylight saving time",
    "famous hoaxes and elaborate cons throughout history",
    "the science of why music gives us chills",
    "the longest unsolved mysteries in mathematics",
    "wild facts about the Roman Empire most people never learn",
    "the weird economics of professional sports",
    "how color perception differs across cultures and languages",
    "the accidental inventions that changed the world",
    "bizarre laws still on the books in US states",
    "the history of competitive eating and food contests",
    "why humans dream and the strangest theories about it",
    "the underground world of competitive puzzle solving",
    "forgotten technologies that almost changed everything",
    "the science of superstitions — what the data actually shows",
    "obscure world records that no one is trying to break",
    "the surprisingly dramatic history of fonts and typography",
    "animals with abilities that seem like science fiction",
    "the odd and fascinating history of board games",
]


def _weekly_seed(local_date: date) -> int:
    iso = local_date.isocalendar()
    return iso[0] * 100 + iso[1]


def is_wildcard_day(local_date: date) -> bool:
    rng = random.Random(_weekly_seed(local_date))
    return local_date.isoweekday() == rng.randint(1, 7)


def pick_wildcard_topic(local_date: date) -> str:
    rng = random.Random(_weekly_seed(local_date) + 1)
    return rng.choice(WILDCARD_TOPICS)
