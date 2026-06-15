# Dashboard Monitoring — Finance & News Analysis

Platform monitoring keuangan berbasis microservice yang mengumpulkan berita finansial, memproses sentimen secara otomatis, dan menyajikan data melalui REST API dan dashboard interaktif.

## Arsitektur

```
┌─────────────────────────────────────────────────────────────────┐
│                        Data Flow                                │
│                                                                 │
│  [Web Sources]                                                  │
│       │                                                         │
│       ▼                                                         │
│  ingestion/scraper  ──► Kafka (raw_*)  ──► processing/transform │
│       │                                         │               │
│       ▼                                         ▼               │
│   MongoDB (raw)                          PostgreSQL (processed) │
│   MinIO (files)                                 │               │
│                                                 ▼               │
│                                          app/api (FastAPI)      │
│                                                 │               │
│                                                 ▼               │
│                                        app/dashboard (React)    │
└─────────────────────────────────────────────────────────────────┘
```

## Struktur Proyek

```
dashboard-monitoring/
│
├── app/
│   ├── api/                        # Backend FastAPI
│   │   ├── core/
│   │   │   └── config.py           # Konfigurasi aplikasi (Pydantic Settings)
│   │   ├── db/
│   │   │   └── session.py          # Setup SQLAlchemy async engine & session
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── article.py
│   │   │   ├── analysis.py
│   │   │   ├── article_storage.py
│   │   │   ├── article_tags.py
│   │   │   ├── base.py             # TimestampMixin
│   │   │   ├── item.py
│   │   │   └── source_model.py
│   │   ├── route/v1/endpoints/     # Router FastAPI
│   │   │   ├── article.py
│   │   │   ├── items.py
│   │   │   └── source.py
│   │   ├── schemas/                # Pydantic request/response schemas
│   │   │   ├── article.py
│   │   │   ├── item.py
│   │   │   ├── response.py         # Generic ResponseSchema[T]
│   │   │   └── source.py
│   │   ├── services/               # Business logic layer
│   │   │   ├── article_service.py
│   │   │   ├── item_service.py
│   │   │   └── source_service.py
│   │   ├── tests/
│   │   │   └── test_items.py
│   │   └── main.py                 # FastAPI app factory & middleware
│   │
│   └── dashboard/                  # Frontend React + Vite + TailwindCSS
│       ├── src/
│       │   ├── components/
│       │   │   ├── charts/         # Chart components
│       │   │   ├── layout/         # Topbar, Sidebar, StatusBar
│       │   │   ├── panels/         # KPI, Heatmap, Signals, dll
│       │   │   └── ui/             # Reusable UI primitives
│       │   ├── hooks/              # Custom React hooks
│       │   ├── pages/              # DashboardPage, NewsPage
│       │   ├── service/            # API client (newsApi.ts)
│       │   ├── types/              # TypeScript types
│       │   └── utils/              # mockData, helpers
│       ├── package.json
│       └── vite.config.ts
│
├── ingestion/                      # Layer pengambilan data
│   └── scraper/
│       ├── extractor.py            # HTTP fetcher (cloudscraper)
│       ├── header.py               # Random user-agent headers
│       ├── parsing.py              # HTML parser + ML link classifier
│       └── scrape.py               # Orchestrator scraping per source
│
├── processing/                     # Layer transformasi data
│   ├── cleaning/
│   │   └── clean.py                # Text cleaning
│   └── transform/
│       ├── extract_features.py     # Ekstraksi topik, keywords, currency pair
│       ├── sentiment_analysis.py   # Prediksi sentimen (HuggingFace)
│       ├── transform.py            # Kafka consumer pipeline (raw → silver)
│       └── translate.py            # Terjemahan teks
│
├── storage/                        # Abstraksi layer storage
│   ├── kafka/
│   │   ├── consumer.py             # NLP Kafka consumer
│   │   └── producer.py             # Kafka producer wrapper
│   ├── minio/
│   │   └── minio.py                # MinIO client (upload/delete JSON)
│   ├── mongo/
│   │   └── mongoservice.py         # MongoDB raw metadata store
│   └── postgres/
│       ├── database.py             # Async SQLAlchemy setup (pipeline)
│       ├── schema.py               # Pydantic schemas untuk pipeline
│       └── models/
│           ├── base.py
│           └── model.py            # ORM models untuk pipeline storage
│
├── ml/                             # Machine learning models
│   └── sentimen_analisis/
│       ├── training.py             # Training script
│       ├── prediction_sentimen.py  # Inference helper
│       ├── stocks_sentimen.py      # Sentimen saham
│       ├── crypto_sentimen.py      # Sentimen crypto
│       └── create_dataset.py       # Dataset builder
│
├── alembic/                        # Database migrations
│   ├── env.py
│   └── versions/
│       ├── 08df190497b4_initial_schema.py
│       └── 2d607ad694a2_create_article_tables.py
│
├── utils/
│   └── time.py                     # Helper waktu (WIB timezone)
│
├── data/                           # Data statis & seed
│   ├── topic.json                  # Konfigurasi topik & keyword
│   ├── data_currencies.csv         # Daftar currency pair
│   ├── data_news_source.json       # Seed data sumber berita
│   └── data.json                   # Sample artikel terproses
│
├── main.py                         # Entry point scraper (async runner)
├── docker-compose.yaml             # Semua service infrastruktur
├── Dockerfile                      # Image Airflow + dependencies
├── pyproject.toml                  # Python dependencies (uv/pip)
├── alembic.ini                     # Konfigurasi Alembic
├── .env.example                    # Template variabel lingkungan
├── .python-version                 # Versi Python (3.14)
└── .gitignore
```

## Tech Stack

| Layer | Teknologi |
|---|---|
| Backend API | FastAPI, SQLAlchemy (async), Alembic |
| Frontend | React, Vite, TypeScript, TailwindCSS |
| Message Broker | Apache Kafka (confluent-kafka) |
| Database | PostgreSQL (artikel), MongoDB (raw metadata) |
| Object Storage | MinIO |
| Orchestration | Apache Airflow (CeleryExecutor) |
| NLP/ML | HuggingFace Transformers, scikit-learn |
| Infra | Docker Compose, Redis |

## Prasyarat

- Python 3.14+
- Node.js 18+
- Docker & Docker Compose
- [uv](https://github.com/astral-sh/uv) (package manager)

## Cara Menjalankan

### 1. Clone & Konfigurasi

```bash
git clone <repo-url>
cd dashboard-monitoring

cp .env.example .env
# Edit .env sesuai environment Anda
```

### 2. Jalankan Infrastruktur

```bash
docker compose up -d postgres redis kafka minio mongo
```

### 3. Setup Backend

```bash
# Install dependencies
uv sync

# Jalankan migrasi database
alembic upgrade head

# Jalankan API server
uvicorn app.api.main:app --reload --port 8000
```

### 4. Jalankan Frontend

```bash
cd app/dashboard
npm install
npm run dev
# Akses di http://localhost:5173
```

### 5. Jalankan Pipeline Scraping

```bash
# Scraper (ambil berita dari semua sumber aktif)
uv run python main.py

# NLP Transform Consumer (proses raw → silver)
uv run python processing/transform/transform.py
```
## API Endpoints

Base URL: `http://localhost:8000`

| Method | Endpoint | Deskripsi |
|---|---|---|
| GET | `/` | Health check |
| GET | `/health` | Status aplikasi |
| GET | `/docs` | Swagger UI |
| GET | `/redoc` | ReDoc |
| **Articles** | | |
| GET | `/articles` | List artikel (pagination) |
| GET | `/articles/{id}` | Detail artikel |
| GET | `/articles/category/{cat}` | Filter by kategori |
| GET | `/articles/sentiment/{s}` | Filter by sentimen |
| **News Sources** | | |
| GET | `/news-sources` | List sumber berita |
| GET | `/news-sources/{id}` | Detail sumber |
| POST | `/news-sources` | Tambah sumber |
| PUT | `/news-sources/{id}` | Update sumber |
| DELETE | `/news-sources/{id}` | Hapus sumber |
| **Items** | | |
| GET | `/items` | List items |
| POST | `/items` | Buat item |
| PUT | `/items/{id}` | Update item |
| DELETE | `/items/{id}` | Hapus item |

## Alur Data

```
1. Scraper (ingestion/scraper/scrape.py)
   └─► Fetch HTML dari news sources (DB)
   └─► Klasifikasi link dengan ML model
   └─► Ekstrak konten artikel (trafilatura)
   └─► Upload ke MinIO (raw-news bucket)
   └─► Insert metadata ke MongoDB
   └─► Publish ke Kafka topic raw_{category}

2. NLP Transform (processing/transform/transform.py)
   └─► Consume Kafka topic raw_{category}
   └─► Baca artikel dari MinIO
   └─► Clean text → analisis sentimen (HuggingFace)
   └─► Ekstrak keywords & topik
   └─► Insert ke PostgreSQL (articles + analysis)
   └─► Publish ke Kafka topic silver_{category}

3. API (app/api)
   └─► Serve data dari PostgreSQL ke dashboard
```

## Konfigurasi Lingkungan

Semua konfigurasi dibaca dari `.env`. Lihat `.env.example` untuk daftar lengkap variabel yang diperlukan.

Variabel wajib:

```
POSTGRES_URL       # Connection string PostgreSQL async
MONGO_URI          # URI MongoDB
KAFKA_BOOTSTRAP_SERVERS
MINIO_ENDPOINT / MINIO_ACCESS_KEY / MINIO_SECRET_KEY / MINIO_BUCKET
```

## Menjalankan Tests

```bash
uv run pytest app/api/tests/ -v
```

## Migrasi Database

```bash
# Buat migrasi baru
alembic revision --autogenerate -m "deskripsi perubahan"

# Terapkan migrasi
alembic upgrade head

# Rollback satu langkah
alembic downgrade -1
```

## Lisensi

Internal project — lihat kebijakan tim untuk detail lisensi.
