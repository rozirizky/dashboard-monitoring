import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.db.session import Base, get_db
from app.api.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    app.dependency_overrides[get_db] = override_get_db
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_item(client):
    resp = await client.post("/api/v1/items", json={"name": "Test Item", "price": 9999.0})
    assert resp.status_code == 201
    data = resp.json()
    assert data["success"] is True
    assert data["data"]["name"] == "Test Item"


@pytest.mark.asyncio
async def test_list_items(client):
    await client.post("/api/v1/items", json={"name": "Item A", "price": 100.0})
    await client.post("/api/v1/items", json={"name": "Item B", "price": 200.0})
    resp = await client.get("/api/v1/items")
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 2


@pytest.mark.asyncio
async def test_get_item(client):
    create = await client.post("/api/v1/items", json={"name": "Item X", "price": 50.0})
    item_id = create.json()["data"]["id"]
    resp = await client.get(f"/api/v1/items/{item_id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["id"] == item_id


@pytest.mark.asyncio
async def test_update_item(client):
    create = await client.post("/api/v1/items", json={"name": "Old Name", "price": 10.0})
    item_id = create.json()["data"]["id"]
    resp = await client.put(f"/api/v1/items/{item_id}", json={"name": "New Name"})
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_item(client):
    create = await client.post("/api/v1/items", json={"name": "To Delete", "price": 1.0})
    item_id = create.json()["data"]["id"]
    resp = await client.delete(f"/api/v1/items/{item_id}")
    assert resp.status_code == 200
    get = await client.get(f"/api/v1/items/{item_id}")
    assert get.status_code == 404


@pytest.mark.asyncio
async def test_item_not_found(client):
    resp = await client.get("/api/v1/items/999999")
    assert resp.status_code == 404
