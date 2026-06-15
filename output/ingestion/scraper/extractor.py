import logging
from datetime import datetime, timedelta, timezone

import cloudscraper
import requests

from ingestion.scraper.header import headers

logger = logging.getLogger(__name__)

_JAKARTA_TZ = timezone(timedelta(hours=7))
_INVESTING_BASE = "https://endpoints.investing.com/pd-instruments/v1/calendars/economic"


def _today_range() -> tuple[str, str]:
    now = datetime.now(_JAKARTA_TZ)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end = now.replace(hour=23, minute=59, second=59, microsecond=999000)
    return start.isoformat(), end.isoformat()


class Extractor:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.scraper = cloudscraper.create_scraper()

    def _fetch(self, endpoint: str, params: dict | None = None):
        try:
            logger.debug("Request -> %s | params=%s", endpoint, params)
            response = self.scraper.get(
                endpoint,
                params=params,
                headers=headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()

            content_type = response.headers.get("Content-Type", "").lower()
            if "application/json" in content_type:
                try:
                    return response.json()
                except ValueError:
                    logger.error("Failed to parse JSON response from %s", endpoint)
                    return None
            return response.text

        except requests.exceptions.Timeout:
            logger.error("Timeout: %s", endpoint)
        except requests.exceptions.ConnectionError:
            logger.error("Connection error: %s", endpoint)
        except requests.exceptions.HTTPError as e:
            logger.error("HTTP error: %s | status=%s | %s", endpoint, response.status_code, e)
        except requests.exceptions.RequestException as e:
            logger.error("Request error: %s | %s", endpoint, e)
        except Exception:
            logger.exception("Unexpected error fetching: %s", endpoint)
        return None

    def news(self, url: str):
        return self._fetch(url)

    def events(self):
        start_date, end_date = _today_range()
        return self._fetch(
            f"{_INVESTING_BASE}/events/occurrences",
            params={
                "domain_id": 1,
                "start_date": start_date,
                "end_date": end_date,
                "limit": 5,
            },
        )

    def occurrences(self, event_id: int):
        return self._fetch(
            f"{_INVESTING_BASE}/events/{event_id}/occurrences",
            params={"domain_id": "1"},
        )
