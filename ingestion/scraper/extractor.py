import logging
from datetime import datetime, timedelta, timezone

import cloudscraper
import requests

from ingestion.scraper.header import headers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger("Extractor")


def get_date() -> tuple[str, str]:
    
    tz = timezone(timedelta(hours=7))
    now = datetime.now(tz)
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = now.replace(hour=23, minute=59, second=59, microsecond=999000)
    return start_date.isoformat(), end_date.isoformat()


class Extractor:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.scraper = cloudscraper.create_scraper()

    def _fetch(self, endpoint: str, params=None):
        try:
            logger.info(f"Request -> {endpoint} | params={params}")

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
                    logger.error("Failed to parse JSON response")
                    return None
            return response.text

        except requests.exceptions.Timeout:
            logger.error(f"Timeout error -> {endpoint}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error -> {endpoint}")
        except requests.exceptions.HTTPError as e:
            logger.error(
                f"HTTP error -> {endpoint} | "
                f"status={response.status_code} | error={e}"
            )
        except requests.exceptions.RequestException as e:
            logger.error(f"Request exception -> {endpoint} | error={e}")
        except Exception as e:
            logger.exception(f"Unexpected error -> {endpoint} | error={e}")

        return None

    def news(self, url: str):
        logger.info("Fetching news...")
        return self._fetch(endpoint=url)

    def events(self):
        logger.info("Fetching events...")
        start_date, end_date = get_date()

        endpoint = (
            "https://endpoints.investing.com/pd-instruments/v1"
            "/calendars/economic/events/occurrences"
        )
        params = {
            "domain_id": 1,
            "start_date": start_date,
            "end_date": end_date,
            "limit": 5,
        }
        return self._fetch(endpoint=endpoint, params=params)

    def occurrences(self, event_id: int):
        logger.info(f"Fetching occurrences for id={event_id}")

        endpoint = (
            f"https://endpoints.investing.com/pd-instruments/v1"
            f"/calendars/economic/events/{event_id}/occurrences"
        )
        params = {"domain_id": "1"}
        return self._fetch(endpoint=endpoint, params=params)
