
from datetime  import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, Float, String,
    DateTime, Boolean, Index, text,
)
from app.api.db.session import Base

class CryptoTrending(Base):
    __tablename__ = "crypto_trending"

    id              = Column(BigInteger, primary_key=True, autoincrement=True)
    fetched_at      = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    rank            = Column(Integer, nullable=False)
    coin_id         = Column(String(100), nullable=False)
    symbol          = Column(String(20),  nullable=False)
    name            = Column(String(200), nullable=False)
    market_cap_rank = Column(Integer,     nullable=True)
    thumb           = Column(String(500), nullable=True)
    price_usd       = Column(Float,       nullable=True)
    change_24h      = Column(Float,       nullable=True)
    volume_24h      = Column(Float,       nullable=True)

    __table_args__ = (
        Index("ix_ct_fetched_at", "fetched_at"),
    )

class CryptoMarket(Base):
    __tablename__ = "crypto_market"

    id              = Column(BigInteger, primary_key=True, autoincrement=True)
    fetched_at      = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    coin_id         = Column(String(100), nullable=False)
    symbol          = Column(String(20),  nullable=False)
    name            = Column(String(200), nullable=False)
    price_usd       = Column(Float,       nullable=True)
    change_24h      = Column(Float,       nullable=True)
    change_7d       = Column(Float,       nullable=True)
    change_30d      = Column(Float,       nullable=True)
    volume_24h      = Column(Float,       nullable=True)
    market_cap      = Column(Float,       nullable=True)
    market_cap_rank = Column(Integer,     nullable=True)

    __table_args__ = (
        Index("ix_cm_fetched_at",        "fetched_at"),
        Index("ix_cm_fetched_at_symbol", "fetched_at", "symbol"),
    )
class StockQuote(Base):
    __tablename__ = "stock_quotes"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    fetched_at  = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    ticker      = Column(String(30),  nullable=False)
    group_name  = Column(String(50),  nullable=False)
    price       = Column(Float,       nullable=True)
    prev_close  = Column(Float,       nullable=True)
    change_pct  = Column(Float,       nullable=True)
    volume      = Column(Float,       nullable=True)
    short_name  = Column(String(200), nullable=True)

    __table_args__ = (
        Index("ix_sq_fetched_at",        "fetched_at"),
        Index("ix_sq_fetched_at_ticker", "fetched_at", "ticker"),
    )
class ForexRate(Base):
    __tablename__ = "forex_rates"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    fetched_at  = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    pair        = Column(String(20),  nullable=False)
    rate        = Column(Float,       nullable=False)
    change_pct  = Column(Float,       nullable=True)
    source      = Column(String(20),  default="yahoo")

    __table_args__ = (
        Index("ix_fr_fetched_at",       "fetched_at"),
        Index("ix_fr_fetched_at_pair",  "fetched_at", "pair"),
    )


class FetchLog(Base):
   
    __tablename__ = "fetch_log"

    id          = Column(BigInteger, primary_key=True, autoincrement=True)
    fetched_at  = Column(DateTime(timezone=True), default=datetime.utcnow)
    source      = Column(String(50),  nullable=False)
    success     = Column(Boolean,     nullable=False)
    rows_saved  = Column(Integer,     default=0)
    duration_ms = Column(Integer,     default=0)
    error_msg   = Column(String(1000),nullable=True)

    __table_args__ = (
        Index("ix_fl_fetched_at", "fetched_at"),
    )

class WatchedAsset(Base):
  
    __tablename__ = "watched_assets"

    id        = Column(Integer,  primary_key=True, autoincrement=True)
    symbol    = Column(String(30),  nullable=False, unique=True)
    name      = Column(String(200), nullable=False)
    category  = Column(String(20),  nullable=False)  
    source    = Column(String(20),  nullable=False)  
    enabled   = Column(Boolean,  default=True)
    added_at  = Column(DateTime(timezone=True), default=datetime.utcnow)

