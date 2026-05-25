"""
Test fixtures: async SQLite engine, session, FastAPI test client.
"""
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.database import Base
from app.api.deps import get_db
from app.core.security import create_access_token, get_password_hash
from app.models import User, UserRole, SPO, SpecialtyTemplate, Specialty, Student

# In-memory async SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture()
async def engine():
    eng = create_async_engine(TEST_DATABASE_URL, echo=False)

    @event.listens_for(eng.sync_engine, "connect")
    def _enable_sqlite_fk(dbapi_connection, _):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield eng
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await eng.dispose()


@pytest.fixture()
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest.fixture()
async def client(engine, db_session) -> AsyncGenerator[AsyncClient, None]:
    """FastAPI test client with overridden DB dependency."""
    # Avoid circular import at module level
    from app.main import app

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


# ---- Data fixtures ----

@pytest.fixture()
async def admin_user(db_session: AsyncSession) -> User:
    user = User(
        login="admin_test",
        password_hash=get_password_hash("admin123"),
        role=UserRole.ADMIN,
        spo_id=None,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture()
async def admin_token(admin_user: User) -> str:
    return create_access_token(data={"sub": str(admin_user.id)})


@pytest.fixture()
async def spo(db_session: AsyncSession) -> SPO:
    spo = SPO(name="Тестовое СПО")
    db_session.add(spo)
    await db_session.commit()
    await db_session.refresh(spo)
    return spo


@pytest.fixture()
async def operator_user(db_session: AsyncSession, spo: SPO) -> User:
    user = User(
        login="operator_test",
        password_hash=get_password_hash("operator123"),
        role=UserRole.OPERATOR,
        spo_id=spo.id,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture()
async def operator_token(operator_user: User) -> str:
    return create_access_token(data={"sub": str(operator_user.id)})


@pytest.fixture()
async def template(db_session: AsyncSession) -> SpecialtyTemplate:
    t = SpecialtyTemplate(code="09.02.07", name="Информационные системы")
    db_session.add(t)
    await db_session.commit()
    await db_session.refresh(t)
    return t


@pytest.fixture()
async def specialty(db_session: AsyncSession, spo: SPO, template: SpecialtyTemplate) -> Specialty:
    s = Specialty(
        spo_id=spo.id,
        template_id=template.id,
        code=template.code,
        name=template.name,
        quota=25,
    )
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)
    return s


@pytest.fixture()
async def student(db_session: AsyncSession, specialty: Specialty) -> Student:
    s = Student(
        specialty_id=specialty.id,
        first_name="Иван",
        last_name="Петров",
        middle_name="Сергеевич",
        certificate_number="1234567890",
    )
    db_session.add(s)
    await db_session.commit()
    await db_session.refresh(s)
    return s
