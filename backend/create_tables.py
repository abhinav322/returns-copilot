from backend.database import Base, engine
from backend.db_models import Order


print("Creating database tables...")

Base.metadata.create_all(
    bind=engine
)

print("Done.")