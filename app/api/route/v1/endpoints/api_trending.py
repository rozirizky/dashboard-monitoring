
from datetime import datetime
from typing   import Optional

from fastapi           import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy        import func, desc

from app.api.models.market import (
    CryptoTrending, CryptoMarket,
    StockQuote, ForexRate, FetchLog,
    get_session,
)

router = APIRouter(prefix="/trending", tags=["trending"])


def _latest_crypto_trending(session) -> list[dict]:
    
    subq = (
        session.query(func.max(CryptoTrending.fetched_at))
        .scalar_subquery()
    )
    rows = (
        session.query(CryptoTrending)
        .filter(CryptoTrending.fetched_at == subq)
        .order_by(CryptoTrending.rank)
        .all()
    )
    return [
        {
            "rank":           r.rank,
            "symbol":         r.symbol,
            "name":           r.name,
            "marketCapRank":  r.market_cap_rank,
            "price":          r.price_usd,
            "change24h":      r.change_24h,
            "volume24h":      r.volume_24h,
            "thumb":          r.thumb,
        }
        for r in rows
    ]


def _latest_crypto_markets(session) -> list[CryptoMarket]:
    subq = (
        session.query(func.max(CryptoMarket.fetched_at))
        .scalar_subquery()
    )
    return (
        session.query(CryptoMarket)
        .filter(CryptoMarket.fetched_at == subq)
        .all()
    )


def _gainers_losers(markets: list[CryptoMarket], period: str = "24h"):
    field_map = {
        "24h": lambda m: m.change_24h,
        "7d":  lambda m: m.change_7d,
        "30d": lambda m: m.change_30d,
    }
    get_chg = field_map.get(period, field_map["24h"])

    valid  = [m for m in markets if get_chg(m) is not None]
    sorted_m = sorted(valid, key=lambda m: get_chg(m), reverse=True)  # type: ignore

    def _row(m: CryptoMarket) -> dict:
        return {
            "symbol":   m.symbol,
            "name":     m.name,
            "price":    m.price_usd,
            "change24h": get_chg(m),
            "volume":   m.volume_24h,
        }

    return {
        "gainers": [_row(m) for m in sorted_m[:5]],
        "losers":  [_row(m) for m in sorted_m[-5:][::-1]],
    }


def _latest_stocks(session) -> list[dict]:
    subq = (
        session.query(func.max(StockQuote.fetched_at))
        .scalar_subquery()
    )
    rows = (
        session.query(StockQuote)
        .filter(StockQuote.fetched_at == subq)
        .order_by(StockQuote.group_name, StockQuote.ticker)
        .all()
    )
    return [
        {
            "ticker":    r.ticker,
            "group":     r.group_name,
            "price":     r.price,
            "prevClose": r.prev_close,
            "change":    r.change_pct,
            "volume":    r.volume,
            "shortName": r.short_name,
        }
        for r in rows
    ]


def _latest_forex(session) -> list[dict]:
    subq = (
        session.query(func.max(ForexRate.fetched_at))
        .scalar_subquery()
    )
    rows = (
        session.query(ForexRate)
        .filter(ForexRate.fetched_at == subq)
        .order_by(ForexRate.pair)
        .all()
    )
    return [
        {
            "pair":   r.pair,
            "rate":   r.rate,
            "change": r.change_pct,
            "source": r.source,
        }
        for r in rows
    ]


def _fetch_timestamps(session) -> dict:
    
    sources = ["coingecko_trending", "coingecko_market", "yfinance_stocks", "forex"]
    result  = {}
    for src in sources:
        row = (
            session.query(FetchLog)
            .filter(FetchLog.source == src, FetchLog.success == True)  # noqa: E712
            .order_by(desc(FetchLog.fetched_at))
            .first()
        )
        result[src] = row.fetched_at.isoformat() if row else None
    return result


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/crypto")
def get_crypto():
    session = get_session()
    try:
        trending = _latest_crypto_trending(session)
        markets  = _latest_crypto_markets(session)
        gl       = _gainers_losers(markets)
        return {
            "trending":    trending,
            "gainers":     gl["gainers"],
            "losers":      gl["losers"],
            "lastUpdated": datetime.utcnow().isoformat(),
        }
    finally:
        session.close()


@router.get("/stocks")
def get_stocks():
    session = get_session()
    try:
        return {
            "stocks":      _latest_stocks(session),
            "lastUpdated": datetime.utcnow().isoformat(),
        }
    finally:
        session.close()


@router.get("/forex")
def get_forex():
    session = get_session()
    try:
        return {
            "forex":       _latest_forex(session),
            "lastUpdated": datetime.utcnow().isoformat(),
        }
    finally:
        session.close()


@router.get("/heatmap")
def get_heatmap(period: str = Query("24h", pattern="^(24h|7d|30d)$")):
    session = get_session()
    try:
        markets = _latest_crypto_markets(session)
        gl      = _gainers_losers(markets, period)

        field_map = {
            "24h": lambda m: m.change_24h,
            "7d":  lambda m: m.change_7d,
            "30d": lambda m: m.change_30d,
        }
        get_chg = field_map[period]

        # Ambil juga forex + stock snapshot untuk heatmap gabungan
        forex  = _latest_forex(session)
        stocks = _latest_stocks(session)

        crypto_cells = [
            {
                "symbol":   m.symbol,
                "name":     m.name,
                "change":   get_chg(m),
                "category": "crypto",
                "weight":   _crypto_weight(m.coin_id, m.market_cap_rank),
            }
            for m in markets
            if get_chg(m) is not None
        ]

        forex_cells = [
            {
                "symbol":   f["pair"],
                "name":     f["pair"],
                "change":   f["change"],
                "category": "forex",
                "weight":   1,
            }
            for f in forex
            if f["change"] is not None
        ]

        stock_cells = [
            {
                "symbol":   s["ticker"].replace(".JK", "").replace("^", ""),
                "name":     s["shortName"] or s["ticker"],
                "change":   s["change"],
                "category": "stock",
                "weight":   _stock_weight(s["ticker"]),
            }
            for s in stocks
            if s["change"] is not None
        ]

        return {
            "cells":       crypto_cells + stock_cells + forex_cells,
            "period":      period,
            "lastUpdated": datetime.utcnow().isoformat(),
        }
    finally:
        session.close()


def _crypto_weight(coin_id: str, rank: Optional[int]) -> int:
    BIG = {"bitcoin": 6, "ethereum": 5, "binancecoin": 3, "solana": 3}
    if coin_id in BIG:
        return BIG[coin_id]
    if rank and rank <= 5:
        return 3
    if rank and rank <= 20:
        return 2
    return 1


def _stock_weight(ticker: str) -> int:
    BIG = {"NVDA", "AAPL", "MSFT", "^GSPC"}
    return 3 if ticker in BIG else 2 if not ticker.endswith(".JK") else 1


@router.get("/all")
def get_all():
    session = get_session()
    try:
        trending = _latest_crypto_trending(session)
        markets  = _latest_crypto_markets(session)
        gl       = _gainers_losers(markets)
        stocks   = _latest_stocks(session)
        forex    = _latest_forex(session)
        ts       = _fetch_timestamps(session)

        return {
            "crypto": {
                "trending": trending,
                "gainers":  gl["gainers"],
                "losers":   gl["losers"],
            },
            "stocks": stocks,
            "forex":  forex,
            "fetchedAt": ts,
            "lastUpdated": datetime.utcnow().isoformat(),
        }
    finally:
        session.close()


@router.get("/status")
def get_status():
    
    session = get_session()
    try:
        ts = _fetch_timestamps(session)

        # 5 log terakhir
        recent = (
            session.query(FetchLog)
            .order_by(desc(FetchLog.fetched_at))
            .limit(20)
            .all()
        )
        logs = [
            {
                "source":    r.source,
                "success":   r.success,
                "rows":      r.rows_saved,
                "durationMs":r.duration_ms,
                "error":     r.error_msg,
                "at":        r.fetched_at.isoformat(),
            }
            for r in recent
        ]

        return {
            "status":     "ok",
            "fetchedAt":  ts,
            "recentLogs": logs,
        }
    finally:
        session.close()