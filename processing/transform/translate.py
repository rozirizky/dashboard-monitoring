from deep_translator import GoogleTranslator
from loguru import logger

class Translate:
    def __init__(self):
        logger.debug("Inisialisasi GoogleTranslator...")
        self.translated =  GoogleTranslator(source='auto', target='en')

    def translate_text(self ,text, chunk_size=4500):
        text_len = len(text)

        if text_len <= chunk_size:
            logger.debug(f"Teks pendek ({text_len} chars), translate langsung")
            result = self.translated.translate(text)
            logger.debug("Translasi selesai")
            return result

        
        chunks = []
        remaining = text

        while remaining:
            if len(remaining) <= chunk_size:
                chunks.append(remaining)
                break
            chunk = remaining[:chunk_size]
            last_space = chunk.rfind(' ')
            if last_space != -1:
                chunk = chunk[:last_space]
            chunks.append(chunk)
            remaining = remaining[len(chunk):].lstrip()

        logger.info(f"Teks panjang ({text_len} chars), dibagi menjadi {len(chunks)} chunk")

        translated = []
        for i, chunk in enumerate(chunks):
            logger.debug(f"Translating chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...")
            translated.append(self.translated.translate(chunk))

        logger.debug("Semua chunk berhasil ditranslasi")
        return ' '.join(translated)
