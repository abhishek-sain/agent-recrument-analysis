"""
Quick local dev helper: creates all tables directly from the SQLAlchemy
models (no migration history), plus the SQL Server SEQUENCE objects the
app uses to generate ids like TKT-12-09-2026-143059-7. Use Alembic
instead for anything beyond a first local run - see README.

Usage:
    python -m scripts.init_db
"""

from sqlalchemy import text

from app.database import Base, engine
from app import models  # noqa: F401
from app.services.id_generator import SEQ_DOCUMENT_DETAILS, SEQ_USERS_DATA

SEQUENCES = [SEQ_USERS_DATA, SEQ_DOCUMENT_DETAILS]


def create_sequences():
    with engine.begin() as conn:
        for seq_name in SEQUENCES:
            exists = conn.execute(
                text("SELECT 1 FROM sys.sequences WHERE name = :name"), {"name": seq_name}
            ).first()
            if not exists:
                conn.execute(text(f"CREATE SEQUENCE {seq_name} START WITH 1 INCREMENT BY 1"))


def main():
    Base.metadata.create_all(bind=engine)
    create_sequences()
    print("Tables and sequences created.")


if __name__ == "__main__":
    main()
