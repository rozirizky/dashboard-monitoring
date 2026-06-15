import asyncio
import json
import logging
import traceback
import warnings
from pathlib import Path
from typing import Optional
from urllib.parse import urlsplit

import joblib
import pandas as pd
import trafilatura
from bs4 import BeautifulSoup
from trafilatura.settings import Extractor

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

logger = logging.getLogger("Parser")

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "model/link_classifier/link_classifier.pkl"
FEATURES_MODULE = BASE_DIR / "model/link_classifier/extra_features.py"


def _load_extract_features():
    """Lazy-load extract_features dari model/link_classifier."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "extra_features", FEATURES_MODULE
    )
    mod = importlib.util.load_from_spec(spec)  # type: ignore
    spec.loader.exec_module(mod)  # type: ignore
    return mod.extract_features


class Parser:
    def __init__(self):
        try:
            self.model, self.features = joblib.load(MODEL_PATH)
            logger.info(f"Model klasifikasi berhasil dimuat dari {MODEL_PATH}")
        except FileNotFoundError:
            logger.critical(
                f"File model tidak ditemukan: {MODEL_PATH}. "
                "Pastikan folder model/ sudah ada (lihat README)."
            )
            raise
        except Exception as e:
            logger.critical(f"Gagal memuat model: {e}")
            logger.debug(traceback.format_exc())
            raise

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "extra_features", FEATURES_MODULE
            )
            mod = importlib.util.module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(mod)  # type: ignore
            self._extract_features = mod.extract_features
        except Exception as e:
            logger.critical(f"Gagal memuat extra_features dari model/: {e}")
            raise

    def _is_same_domain(self, href: str, base: str) -> bool:
        try:
            base_netloc = urlsplit(base).netloc
            href_netloc = urlsplit(href).netloc
            if not href_netloc:
                return True
            return href_netloc == base_netloc
        except Exception:
            return False

    def _classify_link(self, tag, base: str) -> Optional[dict]:
        href = tag.get("href")
        if not href:
            return None

        if not self._is_same_domain(href, base):
            logger.debug(f"Domain tidak cocok, dilewati: {href}")
            return None

        try:
            data = {"link": href, "text": tag.text.strip(), "baselink": base}
            feature = self._extract_features(data=data)
            X = pd.DataFrame([feature], columns=self.features)
            y_pred = self.model.predict(X)[0]
            return data if y_pred == 1 else None
        except Exception as e:
            logger.warning(f"Gagal klasifikasi link '{href}': {e}")
            logger.debug(traceback.format_exc())
            return None

    async def get_url(self, html: str, base: str) -> list[dict]:
        if not html:
            logger.warning("get_url dipanggil dengan HTML kosong")
            return []

        soup = BeautifulSoup(html, "lxml")
        all_links = soup.select("a")
        logger.debug(f"Total tag <a> ditemukan: {len(all_links)}")

        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(None, self._classify_link, tag, base)
            for tag in all_links
        ]
        results = await asyncio.gather(*tasks)

        relevant_links = []
        seen_links = set()
        duplicates = skipped = 0

        for href_result in results:
            if href_result is None:
                skipped += 1
                continue

            normalized = href_result["link"].rstrip("/").split("#")[0]
            if normalized in seen_links:
                duplicates += 1
                continue

            seen_links.add(normalized)
            relevant_links.append(href_result)
            logger.debug(f"Link relevan: {href_result['link']}")

        logger.info(
            f"Klasifikasi selesai | relevan={len(relevant_links)} "
            f"duplikat={duplicates} dilewati={skipped} total={len(all_links)}"
        )
        return relevant_links

    async def get_content(self, html: str) -> Optional[dict]:
        if not html:
            logger.warning("get_content dipanggil dengan HTML kosong")
            return None

        options = Extractor(output_format="json", only_with_metadata=True)
        loop = asyncio.get_event_loop()

        try:
            extracted = await loop.run_in_executor(
                None, lambda: trafilatura.extract(html, options=options)
            )

            if extracted is None:
                logger.warning("trafilatura tidak menemukan konten yang valid")
                return None

            data = json.loads(extracted)
            logger.debug(f"Konten berhasil diekstrak | judul={data.get('title', '-')}")
            return data

        except json.JSONDecodeError as e:
            logger.error(f"Gagal parse JSON dari trafilatura: {e}")
            logger.debug(traceback.format_exc())
            return None
        except Exception as e:
            logger.error(f"Error tak terduga saat ekstrak konten: {e}")
            logger.debug(traceback.format_exc())
            return None
