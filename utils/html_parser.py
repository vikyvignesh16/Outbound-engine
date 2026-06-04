import re
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self._parts.append(data)

    def handle_starttag(self, tag: str, attrs: list) -> None:
        if tag in ("br", "p", "div", "tr", "li", "h1", "h2", "h3", "h4", "h5", "h6"):
            self._parts.append("\n")

    def get_text(self) -> str:
        return "".join(self._parts)


_QUOTE_DIVIDER = re.compile(r"^on .+wrote\s*:?\s*$", re.IGNORECASE)
_SIG_DIVIDER   = re.compile(r"^(-{2,}|_{3,})$")


def strip_reply(raw: str) -> str:
    if not raw:
        return ""

    # Step 1 — HTML → plain text
    if "<" in raw and ">" in raw:
        extractor = _TextExtractor()
        extractor.feed(raw)
        text = extractor.get_text()
    else:
        text = raw

    # Step 2 & 3 — walk lines, drop quoted history and signatures
    clean: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()

        # quoted history: ">" prefix or "On ... wrote:" divider
        if stripped.startswith(">"):
            break
        if _QUOTE_DIVIDER.match(stripped):
            break

        # signature delimiter
        if _SIG_DIVIDER.match(stripped):
            break

        clean.append(line)

    # collapse excessive blank lines and trim
    result = "\n".join(clean)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()
