"""Reset admin password to admin123 for testing."""
import sys
sys.path.insert(0, "backend")

# Import all models to ensure SQLAlchemy can resolve relationships
from app.models import *  # noqa
from app.models.user import User
from app.models.supported_village import *  # noqa
from app.models.project import Project  # noqa
from app.models.fund import Fund  # noqa
from app.core.database import SessionLocal
from app.core.security import get_password_hash

db = SessionLocal()
u = db.query(User).filter(User.username == "admin").first()
if u:
    u.hashed_password = get_password_hash("admin123")
    db.commit()
    print(f"Password reset for admin (id={u.id})")
else:
    print("Admin user not found!")
db.close()
