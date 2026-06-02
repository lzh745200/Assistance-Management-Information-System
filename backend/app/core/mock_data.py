"""Mock data generators.

Provides factory functions for creating sample / seed data during
development and testing.  None of these touch the database directly;
they only return ORM instances that can be flushed by the caller.
"""

import logging
import random
import string
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Random value helpers
# ---------------------------------------------------------------------------

_VILLAGE_NAMES = [
    "桃花村", "青山村", "溪口村", "梅林村", "竹园村",
    "龙井村", "双河村", "石桥村", "枫树村", "云山村",
]

_CATEGORIES = [
    "基础设施", "产业扶持", "教育帮扶", "医疗保障",
    "生态保护", "文化传承", "技能培训", "金融服务",
]


def _random_date(days_ago: int = 365) -> datetime:
    """Return a random datetime within the past *days_ago* days."""
    delta = timedelta(days=random.randint(0, days_ago))
    return datetime.now(timezone.utc) - delta


def _random_string(length: int = 10) -> str:
    """Return a random alphanumeric string."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


def _random_phone() -> str:
    """Return a random Chinese mobile phone number."""
    prefixes = ["138", "139", "158", "159", "186", "188"]
    return random.choice(prefixes) + "".join(random.choices(string.digits, k=8))


def _random_id_card() -> str:
    """Return a plausible (but not cryptographically valid) 18-digit ID number."""
    return "".join(random.choices(string.digits, k=17)) + "X"


# ---------------------------------------------------------------------------
# Mock user data
# ---------------------------------------------------------------------------


def create_mock_user(
    *,
    username: Optional[str] = None,
    role: str = "viewer",
    is_active: bool = True,
) -> Dict[str, Any]:
    """Return a dict representing a mock user.

    Args:
        username: Optional username; auto-generated if not provided.
        role: User role (default ``"viewer"``).
        is_active: Whether the account is active.

    Returns:
        A dict suitable for creating a User ORM instance.
    """
    name = username or f"user_{_random_string(8)}"
    return {
        "username": name,
        "password_hash": "hashed_mock_password",
        "real_name": f"测试_{name}",
        "role": role,
        "is_active": is_active,
        "phone": _random_phone(),
        "email": f"{name}@example.com",
        "id_card": _random_id_card(),
        "created_at": _random_date(),
    }


def create_mock_users(count: int = 10) -> List[Dict[str, Any]]:
    """Create a list of mock users with varying roles.

    Args:
        count: Number of users to generate.

    Returns:
        List of user dicts.
    """
    roles = ["admin", "manager", "operator", "viewer"]
    return [
        create_mock_user(username=f"user_{i:04d}", role=random.choice(roles))
        for i in range(count)
    ]


# ---------------------------------------------------------------------------
# Mock villages / projects
# ---------------------------------------------------------------------------


def create_mock_village(
    *,
    name: Optional[str] = None,
    region: str = "西南地区",
) -> Dict[str, Any]:
    """Return a dict representing a mock village.

    Args:
        name: Village name; random from a preset list if not given.
        region: Geographic region.

    Returns:
        A dict suitable for creating a Village ORM instance.
    """
    return {
        "name": name or random.choice(_VILLAGE_NAMES),
        "region": region,
        "population": random.randint(200, 5000),
        "description": f"这是一个位于{region}的帮扶村落。",
        "created_at": _random_date(),
    }


def create_mock_villages(count: int = 8) -> List[Dict[str, Any]]:
    """Create a list of mock villages."""
    return [create_mock_village() for _ in range(count)]


# ---------------------------------------------------------------------------
# Mock helpers
# ---------------------------------------------------------------------------


def seed_id() -> str:
    """Generate a short unique ID suitable for mock records."""
    return uuid.uuid4().hex[:12]


def random_status(choices: Optional[List[str]] = None) -> str:
    """Pick a random status string from a list.

    Args:
        choices: List of status strings. Defaults to common workflow states.
    """
    if choices is None:
        choices = ["待审核", "审核中", "已通过", "已驳回", "执行中", "已完成"]
    return random.choice(choices)


def random_amount(min_val: float = 1000, max_val: float = 500000) -> float:
    """Return a random funding amount between *min_val* and *max_val*."""
    return round(random.uniform(min_val, max_val), 2)
