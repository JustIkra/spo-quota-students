"""
Tests for service layer.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.user_service import (
    generate_login,
    generate_password,
    authenticate_user,
)
from app.core.security import get_password_hash
from app.models import User, UserRole


@pytest.mark.asyncio
async def test_generate_login_basic(db_session: AsyncSession):
    login = await generate_login("Тестовое СПО", db_session)
    assert login == "testovoe_spo"


@pytest.mark.asyncio
async def test_generate_login_uniqueness(db_session: AsyncSession):
    # Create first user with expected login
    user = User(
        login="testovoe_spo",
        password_hash=get_password_hash("test"),
        role=UserRole.OPERATOR,
    )
    db_session.add(user)
    await db_session.commit()

    # Should get suffixed login
    login = await generate_login("Тестовое СПО", db_session)
    assert login == "testovoe_spo_1"


@pytest.mark.asyncio
async def test_generate_login_empty_name(db_session: AsyncSession):
    login = await generate_login("!!!", db_session)
    assert login == "operator"


@pytest.mark.asyncio
async def test_generate_login_uses_quoted_tail(db_session: AsyncSession):
    login = await generate_login(
        "Государственное профессиональное образовательное учреждение "
        "Ростовской области «Азовский многопрофильный техникум»",
        db_session,
    )
    assert login.startswith("azovskiy")
    assert "gosudarstvennoe" not in login


@pytest.mark.asyncio
async def test_generate_login_straight_quotes(db_session: AsyncSession):
    login = await generate_login('ГБПОУ РО "Донской педагогический колледж"', db_session)
    assert login.startswith("donskoy")


@pytest.mark.asyncio
async def test_generate_password():
    pwd = generate_password()
    assert len(pwd) == 12
    assert any(c.isdigit() for c in pwd)
    assert any(c.isupper() for c in pwd)
    assert any(c.islower() for c in pwd)


@pytest.mark.asyncio
async def test_authenticate_user_success(db_session: AsyncSession):
    user = User(
        login="auth_test",
        password_hash=get_password_hash("secret"),
        role=UserRole.OPERATOR,
    )
    db_session.add(user)
    await db_session.commit()

    result = await authenticate_user(db_session, "auth_test", "secret")
    assert result is not None
    assert result.login == "auth_test"


@pytest.mark.asyncio
async def test_authenticate_user_wrong_password(db_session: AsyncSession):
    user = User(
        login="auth_test2",
        password_hash=get_password_hash("secret"),
        role=UserRole.OPERATOR,
    )
    db_session.add(user)
    await db_session.commit()

    result = await authenticate_user(db_session, "auth_test2", "wrong")
    assert result is None


@pytest.mark.asyncio
async def test_authenticate_user_not_found(db_session: AsyncSession):
    result = await authenticate_user(db_session, "nonexistent", "any")
    assert result is None
