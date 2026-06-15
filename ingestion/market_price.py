
import os
import time
import logging
import requests
from datetime import datetime, timedelta


_YF_CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache", "yfinance")
os.makedirs(_YF_CACHE_DIR, exist_ok=True)
import yfinance as yf
yf.set_tz_cache_location(_YF_CACHE_DIR)


from dotenv import load_dotenv
load_dotenv()

from app.api.db.session import get_sync_session
from app.api.models.market import (
    CryptoTrending, CryptoMarket,
    StockQuote, ForexRate, FetchLog,
    WatchedAsset,
)

logging.basicConfig(
    level  = logging.INFO,
    format = "%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)



COINGECKO_BASE = "https://api.coingecko.com/api/v3"
REQUEST_TIMEOUT  = 15
RATE_LIMIT_SLEEP = 1.5


DEFAULT_STOCK_WATCHLIST: dict[str, list[str]] = {
    "US Tech":   ["NVDA", "AAPL", "MSFT", "GOOGL", "META", "AMZN", "TSLA"],
    "US Index":  ["^GSPC", "^IXIC", "^DJI"],
    "Indonesia": ["BBCA.JK", "BBRI.JK", "TLKM.JK", "ASII.JK", "GOTO.JK", "BMRI.JK"],
}

FOREX_PAIRS: dict[str, str] = {
    "EURUSD=X": "EUR/USD", "GBPUSD=X": "GBP/USD", "USDJPY=X": "USD/JPY",
    "AUDUSD=X": "AUD/USD", "USDCAD=X": "USD/CAD", "USDCHF=X": "USD/CHF",
    "NZDUSD=X": "NZD/USD", "USDIDR=X": "USD/IDR", "USDSGD=X": "USD/SGD",
    "USDCNY=X": "USD/CNY",
}

DATA_RETENTION_HOURS = 48



def _log(session, source: str, ok: bool, rows: int, ms: int, err: str | None = None):
    session.add(FetchLog(
        source=source, success=ok, rows_saved=rows, duration_ms=ms, error_msg=err
    ))
    session.commit()


def _cg_get(path: str, params: dict | None = None):
    resp = requests.get(
        f"{COINGECKO_BASE}/{path.lstrip('/')}",
        params  = params,
        timeout = REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    time.sleep(RATE_LIMIT_SLEEP)
    return resp.json()


def _get_stock_watchlist() -> dict[str, list[str]]:
    """Ambil daftar saham dari DB watched_assets (jika ada), fallback ke default."""
    session = get_sync_session()
    try:
        rows = session.query(WatchedAsset).filter(
            WatchedAsset.category.in_(["stock", "index"]),
            WatchedAsset.enabled == True,
        ).all()
        if not rows:
            return DEFAULT_STOCK_WATCHLIST

        result: dict[str, list[str]] = {}
        for r in rows:
            group = "Indonesia" if r.symbol.endswith(".JK") \
                  else "US Index" if r.symbol.startswith("^") \
                  else "US Tech"
            result.setdefault(group, []).append(r.symbol)
        return result
    finally:
        session.close()


def _get_forex_pairs() -> dict[str, str]:
    """Ambil pairs forex dari DB atau fallback."""
    session = get_sync_session()
    try:
        rows = session.query(WatchedAsset).filter(
            WatchedAsset.category == "forex",
            WatchedAsset.enabled  == True,
        ).all()
        if not rows:
            return FOREX_PAIRS
        return {r.symbol: r.symbol.replace("=X", "").replace(r.symbol[:3], r.symbol[:3]+"/") for r in rows}
    finally:
        session.close()



def fetch_crypto_trending():
    session = get_sync_session()
    t0, src = time.monotonic(), "coingecko_trending"
    try:
        data     = _cg_get("/search/trending")
        coins    = data["coins"][:10]
        coin_ids = [c["item"]["id"] for c in coins]

        prices = _cg_get("/simple/price", {
            "ids":                ",".join(coin_ids),
            "vs_currencies":      "usd",
            "include_24hr_change":"true",
            "include_24hr_vol":   "true",
        })

        now  = datetime.utcnow()
        rows = []
        for i, c in enumerate(coins, 1):
            item = c["item"]
            p    = prices.get(item["id"], {})
            rows.append(CryptoTrending(
                fetched_at      = now,
                rank            = i,
                coin_id         = item["id"],
                symbol          = item["symbol"].upper(),
                name            = item["name"],
                market_cap_rank = item.get("market_cap_rank"),
                thumb           = item.get("thumb"),
                price_usd       = p.get("usd"),
                change_24h      = p.get("usd_24h_change"),
                volume_24h      = p.get("usd_24h_vol"),
            ))

        session.bulk_save_objects(rows)
        session.commit()
        ms = int((time.monotonic() - t0) * 1000)
        _log(session, src, True, len(rows), ms)
        log.info(f"[{src}] ✓ {len(rows)} rows ({ms}ms)")
    except Exception as e:
        session.rollback()
        ms = int((time.monotonic() - t0) * 1000)
        _log(session, src, False, 0, ms, str(e))
        log.error(f"[{src}] ✗ {e}")
    finally:
        session.close()



def fetch_crypto_markets():
    session = get_sync_session()
    t0, src = time.monotonic(), "coingecko_market"
    try:
        data = _cg_get("/coins/markets", {
            "vs_currency":              "usd",
            "order":                    "market_cap_desc",
            "per_page":                 100,
            "page":                     1,
            "sparkline":                "false",
            "price_change_percentage":  "24h,7d,30d",
        })

        now  = datetime.utcnow()
        rows = [
            CryptoMarket(
                fetched_at      = now,
                coin_id         = c["id"],
                symbol          = c["symbol"].upper(),
                name            = c["name"],
                price_usd       = c.get("current_price"),
                change_24h      = c.get("price_change_percentage_24h_in_currency")
                               or c.get("price_change_percentage_24h"),
                change_7d       = c.get("price_change_percentage_7d_in_currency"),
                change_30d      = c.get("price_change_percentage_30d_in_currency"),
                volume_24h      = c.get("total_volume"),
                market_cap      = c.get("market_cap"),
                market_cap_rank = c.get("market_cap_rank"),
            )
            for c in data
        ]

        session.bulk_save_objects(rows)
        session.commit()
        ms = int((time.monotonic() - t0) * 1000)
        _log(session, src, True, len(rows), ms)
        log.info(f"[{src}] ✓ {len(rows)} rows ({ms}ms)")
    except Exception as e:
        session.rollback()
        ms = int((time.monotonic() - t0) * 1000)
        _log(session, src, False, 0, ms, str(e))
        log.error(f"[{src}] ✗ {e}")
    finally:
        session.close()



def fetch_stocks():
    session = get_sync_session()
    t0, src = time.monotonic(), "yfinance_stocks"
    saved   = 0
    try:
        watchlist = _get_stock_watchlist()
        all_pairs = [(ticker, group) for group, tickers in watchlist.items() for ticker in tickers]
        now = datetime.utcnow()
        rows = []
        for ticker, group in all_pairs:
            try:
                info       = yf.Ticker(ticker).fast_info
                price      = getattr(info, "last_price",      None)
                prev       = getattr(info, "previous_close",  None)
                volume     = getattr(info, "three_month_average_volume", None)
                short_name = getattr(info, "long_name", None) or getattr(info, "short_name", None)
                chg_pct    = (price - prev) / prev * 100 if price and prev and prev > 0 else None

                rows.append(StockQuote(
                    fetched_at = now, ticker = ticker, group_name = group,
                    price = price, prev_close = prev, change_pct = chg_pct,
                    volume = volume, short_name = short_name,
                ))
                saved += 1
            except Exception as e:
                log.warning(f"  [{ticker}] skip: {e}")

        session.bulk_save_objects(rows)
        session.commit()
        ms = int((time.monotonic() - t0) * 1000)
        _log(session, src, True, saved, ms)
        log.info(f"[{src}] ✓ {saved}/{len(all_pairs)} tickers ({ms}ms)")
    except Exception as e:
        session.rollback()
        ms = int((time.monotonic() - t0) * 1000)
        _log(session, src, False, saved, ms, str(e))
        log.error(f"[{src}] ✗ {e}")
    finally:
        session.close()



def _forex_yahoo(now: datetime, pairs: dict[str, str]) -> list[ForexRate]:
    rows = []
    for ticker, label in pairs.items():
        try:
            info  = yf.Ticker(ticker).fast_info
            price = getattr(info, "last_price",     None)
            prev  = getattr(info, "previous_close", None)
            chg   = (price - prev) / prev * 100 if price and prev and prev > 0 else None
            if price:
                rows.append(ForexRate(fetched_at=now, pair=label, rate=price, change_pct=chg, source="yahoo"))
        except Exception as e:
            log.warning(f"  [{ticker}] forex skip: {e}")
    return rows


def _forex_erapi(now: datetime) -> list[ForexRate]:
    resp  = requests.get("https://open.er-api.com/v6/latest/USD", timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    rates = resp.json().get("rates", {})
    return [
        ForexRate(fetched_at=now, pair=f"USD/{cur}", rate=rates[cur], change_pct=None, source="er-api")
        for cur in ["EUR","GBP","JPY","AUD","IDR","SGD","CNY","CAD","CHF","NZD"]
        if rates.get(cur)
    ]


def fetch_forex():
    session = get_sync_session()
    t0, src = time.monotonic(), "forex"
    try:
        pairs = _get_forex_pairs()
        now   = datetime.utcnow()
        rows  = _forex_yahoo(now, pairs)
        if len(rows) < 5:
            log.warning("  Yahoo forex kurang data → fallback er-api")
            rows = _forex_erapi(now)

        session.bulk_save_objects(rows)
        session.commit()
        ms = int((time.monotonic() - t0) * 1000)
        _log(session, src, True, len(rows), ms)
        log.info(f"[{src}] ✓ {len(rows)} pairs ({ms}ms)")
    except Exception as e:
        session.rollback()
        ms = int((time.monotonic() - t0) * 1000)
        _log(session, src, False, 0, ms, str(e))
        log.error(f"[{src}] ✗ {e}")
    finally:
        session.close()



def cleanup_old_data(hours: int = DATA_RETENTION_HOURS):
    """Hapus rows time-series lebih dari `hours` jam untuk hemat disk."""
    from sqlalchemy import delete
    cutoff  = datetime.utcnow() - timedelta(hours=hours)
    session = get_sync_session()
    try:
        for Model in [CryptoTrending, CryptoMarket, StockQuote, ForexRate]:
            result = session.execute(delete(Model).where(Model.fetched_at < cutoff))
            session.commit()
            log.info(f"[cleanup] {Model.__tablename__}: {result.rowcount} rows deleted")
    except Exception as e:
        session.rollback()
        log.error(f"[cleanup] ✗ {e}")
    finally:
        session.close()



def run_all():
    log.info("=" * 55)
    log.info("  TRENDING ASSETS FETCHER")
    log.info(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 55)
    for label, fn in [
        ("CoinGecko Trending", fetch_crypto_trending),
        ("CoinGecko Markets",  fetch_crypto_markets),
        ("Stocks",             fetch_stocks),
        ("Forex",              fetch_forex),
        ("Cleanup",            cleanup_old_data),
    ]:
        log.info(f"▶  {label}…")
        fn()
    log.info("  ✅  Selesai")

if __name__ == "__main__":
    from app.api.db.session import sync_engine
    from app.api.models.market   import Base
    Base.metadata.create_all(sync_engine)
    run_all()