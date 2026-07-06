"""Reset admin password and clear login attempts."""
import sys
sys.path.insert(0, "backend")

from app.models import *  # noqa
from app.models.user import User
from app.models.supported_village import *  # noqa
from app.models.project import Project  # noqa
from app.models.fund import Fund  # noqa
from app.models.audit import LoginAttempt  # noqa
from app.core.database import SessionLocal
from app.core.security import get_password_hash, verify_password

db = SessionLocal()

# Clear login attempts
deleted = db.query(LoginAttempt).delete()
print(f"Deleted {deleted} login attempts")

# Reset password
u = db.query(User).filter(User.username == "admin").first()
if u:
    new_hash = get_password_hash("admin123")
    print(f"Old hash: {u.hashed_password[:50]}...")
    u.hashed_password = new_hash
    db.commit()
    print(f"New hash: {u.hashed_password[:50]}...")
    # Verify
    ok = verify_password("admin123", u.hashed_password)
    print(f"Verify password: {ok}")
else:
    print("Admin user not found!")

db.close()
