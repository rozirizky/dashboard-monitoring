import asyncio
import importlib.util
import json
import logging
import traceback
import warnings
from pathlib import Path
from urllib.parse import urlsplit

import joblib
import pandas as pd
import trafilatura
from bs4 import BeautifulSoup
from trafilatura.settings import Extractor

warnings.filterwarnings("ignore", category=UserWarning, module="sklearn")

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BASE_DIR / "model/link_classifier/link_classifier.pkl"
FEATURES_MODULE = BASE_DIR / "model/link_classifier/extra_features.py"


class Parser:
    def __init__(self):
        try:
            self.model, self.features = joblib.load(MODEL_PATH)
            logger.info("Link classifier loaded from %s", MODEL_PATH)
        except FileNotFoundError:
            logger.critical("Model not found: %s — check README for setup.", MODEL_PATH)
            raise
        except Exception:
            logger.critical("Failed to load model", exc_info=True)
            raise

        try:
            spec = importlib.util.spec_from_file_location("extra_features", FEATURES_MODULE)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            self._extract_features = mod.extract_features
        except Exception:
            logger.critical("Failed to load extra_features from model/", exc_info=True)
            raise

    def _is_same_domain(self, href: str, base: str) -> bool:
        try:
            base_netloc = urlsplit(base).netloc
            href_netloc = urlsplit(href).netloc
            return not href_netloc or href_netloc == base_netloc
        except Exception:
            return False

    def _classify_link(self, tag, base: str) -> dict | None:
        href = tag.get("href")
        if not href or not self._is_same_domain(href, base):
            return None

        try:
            data = {"link": href, "text": tag.text.strip(), "baselink": base}
            feature = self._extract_features(data=data)
            X = pd.DataFrame([feature], columns=self.features)
            return data if self.model.predict(X)[0] == 1 else None
        except Exception as e:
            logger.warning("Link classification failed '%s': %s", href, e)
            return None

    async def get_url(self, html: str, base: str) -> list[dict]:
        if not html:
            logger.warning("get_url called with empty HTML")
            return []

        soup = BeautifulSoup(html, "lxml")
        all_links = soup.select("a")

        loop = asyncio.get_event_loop()
        results = await asyncio.gather(
            *[loop.run_in_executor(None, self._classify_link, tag, base) for tag in all_links]
        )

        relevant = []
        seen = set()
        for item in results:
            if item is None:
                continue
            normalized = item["link"].rstrip("/").split("#")[0]
            if normalized in seen:
                continue
            seen.add(normalized)
            relevant.append(item)

        logger.info("Links: %d relevant / %d total", len(relevant), len(all_links))
        return relevant

    async def get_content(self, html: str) -> dict | None:
        if not html:
            logger.warning("get_content called with empty HTML")
            return None

        options = Extractor(output_format="json", only_with_metadata=True)
        loop = asyncio.get_event_loop()

        try:
            extracted = await loop.run_in_executor(
                None, lambda: trafilatura.extract(html, options=options)
            )
            if extracted is None:
                logger.warning("trafilatura found no valid content")
                return None
            return json.loads(extracted)
        except json.JSONDecodeError as e:
            logger.error("JSON parse error from trafilatura: %s", e)
        except Exception:
            logger.error("Unexpected error extracting content", exc_info=True)
        return None
