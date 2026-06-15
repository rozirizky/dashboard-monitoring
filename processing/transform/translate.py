import logging

from deep_translator import GoogleTranslator

logger = logging.getLogger(__name__)

CHUNK_SIZE = 4500


class Translate:
    def __init__(self):
        self._translator = GoogleTranslator(source="auto", target="en")

    def translate_text(self, text: str) -> str:
        if len(text) <= CHUNK_SIZE:
            return self._translator.translate(text)

        chunks = []
        remaining = text
        while remaining:
            if len(remaining) <= CHUNK_SIZE:
                chunks.append(remaining)
                break
            chunk = remaining[:CHUNK_SIZE]
            last_space = chunk.rfind(" ")
            if last_space != -1:
                chunk = chunk[:last_space]
            chunks.append(chunk)
            remaining = remaining[len(chunk):].lstrip()

        logger.info("Translating %d chunks (%d chars total)", len(chunks), len(text))
        return " ".join(self._translator.translate(c) for c in chunks)
