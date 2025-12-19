import re


def parse_scores(text: str) -> tuple[int, int, int] | None:
    # ищем "Scores: 7/8/6" или "readability=7 correctness=8 efficiency=6"
    m = re.search(r"Scores\s*:\s*(\d+)\s*/\s*(\d+)\s*/\s*(\d+)", text, re.IGNORECASE)
    if m:
        a, b, c = map(int, m.groups())
        return a, b, c

    m = re.search(
        r"readability\s*=?\s*(\d+).*correctness\s*=?\s*(\d+).*efficiency\s*=?\s*(\d+)",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    if m:
        a, b, c = map(int, m.groups())
        return a, b, c

    return None
