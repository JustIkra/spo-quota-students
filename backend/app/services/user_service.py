"""
User service - business logic for user operations.
"""
import re
import secrets
import string
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User, UserRole
from app.core.security import get_password_hash, verify_password


def _extract_meaningful_part(spo_name: str) -> str:
    """Pick the distinguishing tail of the SPO name (text inside quotes if present)."""
    match = re.search(r'[«"„"\'`]([^«»"„"\'`]+)[»"""\'`]', spo_name)
    if match:
        return match.group(1)
    return spo_name


async def generate_login(spo_name: str, db: AsyncSession) -> str:
    """Generate unique login for operator based on SPO name."""
    transliteration = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        ' ': '_', '-': '_'
    }

    source = _extract_meaningful_part(spo_name)

    base_login = ""
    for char in source.lower():
        if char in transliteration:
            base_login += transliteration[char]
        elif char.isalnum():
            base_login += char

    base_login = re.sub(r'_+', '_', base_login).strip('_')

    if len(base_login) > 30:
        truncated = base_login[:30]
        last_sep = truncated.rfind('_')
        if last_sep >= 10:
            truncated = truncated[:last_sep]
        base_login = truncated.strip('_')

    if not base_login:
        base_login = "operator"

    # Check uniqueness and add suffix if needed
    login = base_login
    counter = 1
    max_attempts = 100
    while True:
        result = await db.execute(select(User).where(User.login == login))
        if result.scalars().first() is None:
            break
        login = f"{base_login}_{counter}"
        counter += 1
        if counter > max_attempts:
            raise RuntimeError(f"Could not generate unique login after {max_attempts} attempts")

    return login


def generate_password(length: int = 12) -> str:
    """Generate secure random password."""
    alphabet = string.ascii_letters + string.digits
    # Ensure at least one digit and one letter
    password = [
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.digits),
    ]
    password += [secrets.choice(alphabet) for _ in range(length - 3)]
    secrets.SystemRandom().shuffle(password)
    return ''.join(password)


async def create_operator(db: AsyncSession, spo_id: int, spo_name: str) -> tuple[User, str]:
    """Create operator for SPO with generated credentials."""
    login = await generate_login(spo_name, db)
    password = generate_password()

    user = User(
        login=login,
        password_hash=get_password_hash(password),
        role=UserRole.OPERATOR,
        spo_id=spo_id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user, password


async def reset_password(db: AsyncSession, user_id: int) -> tuple[User, str]:
    """Reset password for user, returning user and new password."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise ValueError("User not found")

    password = generate_password()
    user.password_hash = get_password_hash(password)
    await db.commit()
    await db.refresh(user)

    return user, password


async def authenticate_user(db: AsyncSession, login: str, password: str) -> Optional[User]:
    """Authenticate user by login and password."""
    result = await db.execute(select(User).where(User.login == login))
    user = result.scalars().first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def get_user_by_login(db: AsyncSession, login: str) -> Optional[User]:
    """Get user by login."""
    result = await db.execute(select(User).where(User.login == login))
    return result.scalars().first()
