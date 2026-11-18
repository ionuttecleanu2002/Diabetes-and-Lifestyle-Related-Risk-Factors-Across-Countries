from app.database import Base, engine
from app import models


def create_tables():
    if engine is None:
        raise RuntimeError("DATABASE_URL is not configured in .env")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    create_tables()