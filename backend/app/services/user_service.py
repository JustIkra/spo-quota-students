"""
User service - business logic for user operations.
"""
import secrets
import string
from typing import Optional

from sqlalchemy.orm import Session

from app.models import User, UserRole
from app.core.security import get_password_hash, verify_password


def generate_login(spo_name: str, db: Session) -> str:
    """Generate unique login for operator based on SPO name."""
    # Transliterate and clean SPO name
    transliteration = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        ' ': '_', '-': '_'
    }

    base_login = ""
    for char in spo_name.lower():
        if char in transliteration:
            base_login += transliteration[char]
        elif char.isalnum():
            base_login += char

    # Limit length and clean up
    base_login = base_login[:20].strip('_')
    if not base_login:
        base_login = "operator"

    # Check uniqueness and add suffix if needed
    login = base_login
    counter = 1
    while db.query(User).filter(User.login == login).first():
        login = f"{base_login}_{counter}"
        counter += 1

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


def create_operator(db: Session, spo_id: int, spo_name: str) -> tuple[User, str]:
    """Create operator for SPO with generated credentials."""
    login = generate_login(spo_name, db)
    password = generate_password()

    user = User(
        login=login,
        password_hash=get_password_hash(password),
        role=UserRole.OPERATOR,
        spo_id=spo_id
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return user, password


def authenticate_user(db: Session, login: str, password: str) -> Optional[User]:
    """Authenticate user by login and password."""
    user = db.query(User).filter(User.login == login).first()
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_login(db: Session, login: str) -> Optional[User]:
    """Get user by login."""
    return db.query(User).filter(User.login == login).first()
