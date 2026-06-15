# Finance Dashboard

Platform agregasi berita keuangan dengan data pasar real-time. Terdiri dari scraper, pipeline NLP, market data scheduler, REST API, dan dashboard React.

## Arsitektur

```
Scraper ──► Kafka ──► Transform (NLP) ──► PostgreSQL
                                      └──► MongoDB (raw)
                                      └──► MinIO (artikel)

Scheduler ──► PostgreSQL (market data: crypto, stocks, forex)

FastAPI ──► Dashboard (React + Vite)
```

## Services

| Service       | Port  | Keterangan                              |
|---------------|-------|-----------------------------------------|
| `api`         | 8000  | REST API FastAPI                        |
| `dashboard`   | 3000  | Frontend React via Nginx                |
| `scheduler`   | -     | Market data (CoinGecko, Yahoo Finance)  |
| `transform`   | -     | Kafka consumer + NLP pipeline           |
| `postgres`    | 5432  | Database utama                          |
| `mongo`       | 27017 | Metadata artikel mentah                 |
| `kafka`       | 9092  | Message broker                          |
| `minio`       | 9000  | Object storage artikel (UI: 9001)       |

## Quickstart

### 1. Persiapan environment

```bash
cp .env.example .env
# Edit .env sesuai kebutuhan
```

### 2. Jalankan semua service

```bash
docker compose up -d
```

### 3. Jalankan migrasi database

```bash
docker compose exec api alembic upgrade head
```

### 4. Akses

- **Dashboard:** http://localhost:3000
- **API docs:** http://localhost:8000/docs
- **MinIO console:** http://localhost:9001

## Development (tanpa Docker)

### Backend

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -e .

# Jalankan API
uvicorn app.api.main:app --reload

# Jalankan scheduler
python -m ingestion.scheduler

# Jalankan transform
python -m processing.transform.transform

# Jalankan scraper sekali
python main.py
```

### Frontend

```bash
cd app/dashboard
npm install
npm run dev
```

## Struktur Proyek

```
.
├── app/
│   ├── api/                    # FastAPI backend
│   │   ├── core/config.py      # Settings
│   │   ├── db/session.py       # Database session
│   │   ├── models/             # SQLAlchemy models
│   │   ├── route/v1/endpoints/ # API endpoints
│   │   ├── schemas/            # Pydantic schemas
│   │   └── services/           # Business logic
│   └── dashboard/              # React + Vite frontend
├── ingestion/
│   ├── scraper/                # News scraper
│   ├── market_price.py         # Market data fetcher
│   └── scheduler.py            # APScheduler entrypoint
├── processing/
│   ├── cleaning/               # Text cleaning
│   └── transform/              # NLP pipeline (Kafka consumer)
├── storage/
│   ├── kafka/                  # Kafka producer
│   ├── minio/                  # MinIO client
│   ├── mongo/                  # MongoDB service
│   └── postgres/               # PostgreSQL helpers
├── alembic/                    # Database migrations
├── docker/                     # Nginx config
├── Dockerfile.api
├── Dockerfile.scheduler
├── Dockerfile.transform
├── Dockerfile.dashboard
├── docker-compose.yaml
└── pyproject.toml
```

## API Endpoints

### News Sources
| Method | Path | Keterangan |
|--------|------|------------|
| GET | `/news-sources` | List semua sumber berita |
| GET | `/news-sources/{id}` | Detail sumber |
| POST | `/news-sources` | Tambah sumber baru |
| PUT | `/news-sources/{id}` | Update sumber |
| DELETE | `/news-sources/{id}` | Hapus sumber |

### Articles
| Method | Path | Keterangan |
|--------|------|------------|
| GET | `/articles` | List artikel |
| GET | `/articles/{id}` | Detail artikel |
| GET | `/articles/category/{category}` | Filter by kategori |
| GET | `/articles/sentiment/{sentiment}` | Filter by sentimen |

### Trending / Market Data
| Method | Path | Keterangan |
|--------|------|------------|
| GET | `/trending/crypto` | Data trending & gainers/losers crypto |
| GET | `/trending/stocks` | Harga saham terkini |
| GET | `/trending/forex` | Kurs forex terkini |
| GET | `/trending/heatmap` | Heatmap perubahan harga |
| GET | `/trending/all` | Semua data market sekaligus |
| GET | `/trending/status` | Status fetch terakhir |
