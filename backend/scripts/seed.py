"""Seed de desenvolvimento: usuário demo + créditos + projeto de exemplo.

Idempotente — pode rodar várias vezes. Uso:

    cd backend && python scripts/seed.py
    # ou no docker:
    docker compose run --rm api python scripts/seed.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import Project, ProjectStatus, ProjectStyle, User
from app.security import hash_password

DEMO_EMAIL = "demo@forteshub.com"
DEMO_PASSWORD = "demo12345"
DEMO_CREDITS = 50


def main() -> None:
    # Cria as tabelas se ainda não existirem (conveniência em dev/SQLite).
    Base.metadata.create_all(engine)

    db = SessionLocal()
    try:
        user = db.scalar(select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                password_hash=hash_password(DEMO_PASSWORD),
                credits=DEMO_CREDITS,
            )
            db.add(user)
            db.flush()
            print(f"[seed] usuário criado: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        else:
            if user.credits < DEMO_CREDITS:
                user.credits = DEMO_CREDITS
            print(f"[seed] usuário já existia: {DEMO_EMAIL} (créditos={user.credits})")

        has_project = db.scalar(select(Project).where(Project.user_id == user.id))
        if has_project is None:
            project = Project(
                user_id=user.id,
                status=ProjectStatus.CREATED.value,
                style=ProjectStyle.CARTOON.value,
            )
            db.add(project)
            db.flush()
            print(f"[seed] projeto de exemplo criado: {project.id}")
        else:
            print(f"[seed] projeto de exemplo já existia: {has_project.id}")

        db.commit()
        print(f"[seed] OK. Créditos do demo: {user.credits}")
        print("[seed] login na web/mobile:", DEMO_EMAIL, "/", DEMO_PASSWORD)
    finally:
        db.close()


if __name__ == "__main__":
    main()
