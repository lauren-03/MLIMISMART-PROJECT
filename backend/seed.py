"""Create the tables, the admin account, the knowledge base and demo farmers."""
import sys
from datetime import date, timedelta

from sqlalchemy import func, select

from app.data.knowledge_base import KNOWLEDGE_SEED
from app.config import settings
from app.database import SessionLocal, active_database_url, init_db
from app.models import Farmer, HarvestRecord, KnowledgeItem, Language, Role
from app.security import hash_password

DEMO_FARMERS = [
    # name, phone, location, language, farm size ha, years farming
    ("John Banda",      "0991234567", "Mulanje",  "NY", 1.5, 12),
    ("Grace Phiri",     "0888234567", "Thyolo",   "EN", 2.0, 6),
    ("Samuel Nkhoma",   "0997654321", "Luchenza", "NY", 0.8, 3),
    ("Esnart Chirwa",   "0884567890", "Thekerani", "NY", 3.2, 18),
    ("Chikondi Mwale",  "0995551234", "Bvumbwe",  "NY", 1.1, 9),
    ("Mercy Kalua",     "0886661234", "Lujeri",   "EN", 2.4, 14),
    ("Patrick Nyirenda", "0997771234", "Chitakale", "NY", 0.6, 2),
    ("Loveness Mbewe",  "0889991234", "Khonjeni", "NY", 1.8, 7),
]
DEMO_PASSWORD = "farmer123"


def demo_harvest(farmer_id: int) -> list[HarvestRecord]:
    """A believable year of plucking rounds for the demonstration farmer.

    Rounds are weekly in the rainy season and fortnightly in the dry months,
    with yields following the season, so the harvest chart has a real shape.
    Figures are illustrative, not survey data.
    """
    per_round = {1: 95, 2: 105, 3: 90, 4: 60, 5: 30, 6: 18, 7: 10, 8: 12,
                 9: 22, 10: 28, 11: 55, 12: 80}
    records = []
    day = date.today() - timedelta(days=330)
    while day <= date.today():
        month = day.month
        rainy = month in (11, 12, 1, 2, 3, 4)
        if month != 7 or day.day <= 14:  # main pruning month: little plucking
            wobble = ((day.toordinal() * 37) % 21 - 10) / 100  # deterministic +/-10%
            records.append(HarvestRecord(
                farmer_id=farmer_id, harvest_date=day,
                kg=round(per_round[month] * (1 + wobble), 1),
                price_per_kg=220.0 if day.year < date.today().year else 250.0,
            ))
        day += timedelta(days=7 if rainy else 14)
    return records


def main() -> None:
    init_db()
    print(f"Database: {active_database_url.split('@')[-1]}")
    db = SessionLocal()
    try:
        created = []

        # --- administrator ---
        admin_phone = "".join(c for c in settings.admin_phone if c.isdigit())
        admin = db.scalar(select(Farmer).where(Farmer.phone == admin_phone))
        if not admin:
            db.add(Farmer(
                name="System Administrator",
                phone=admin_phone,
                password_hash=hash_password(settings.admin_password),
                location="Thyolo",
                language=Language.EN,
                role=Role.ADMIN,
            ))
            created.append(f"admin ({admin_phone})")

        # --- demo farmers ---
        for name, phone, location, language, size, years in DEMO_FARMERS:
            if db.scalar(select(Farmer).where(Farmer.phone == phone)):
                continue
            db.add(Farmer(
                name=name,
                phone=phone,
                password_hash=hash_password(DEMO_PASSWORD),
                location=location,
                language=Language(language),
                farm_size_ha=size,
                years_farming=years,
                role=Role.FARMER,
            ))
            created.append(f"farmer {name} ({phone})")

        # --- knowledge base ---
        existing = db.scalar(select(func.count()).select_from(KnowledgeItem)) or 0
        if existing == 0:
            for item in KNOWLEDGE_SEED:
                db.add(KnowledgeItem(**item))
            created.append(f"{len(KNOWLEDGE_SEED)} knowledge items")

        db.commit()

        # --- harvest diary for the demonstration farmer ---
        john = db.scalar(select(Farmer).where(Farmer.phone == "0991234567"))
        if john and not db.scalar(
            select(func.count()).select_from(HarvestRecord)
            .where(HarvestRecord.farmer_id == john.farmer_id)
        ):
            rows = demo_harvest(john.farmer_id)
            db.add_all(rows)
            db.commit()
            created.append(f"{len(rows)} harvest diary entries for John Banda")

        if created:
            print("Created:")
            for entry in created:
                print("  -", entry)
        else:
            print("Nothing to create; the database was already seeded.")

        print()
        print("Sign in with:")
        print(f"  Admin   {admin_phone} / {settings.admin_password}")
        print(f"  Farmer  0991234567 / {DEMO_PASSWORD}   (Mulanje, Chichewa)")
        print(f"  Farmer  0888234567 / {DEMO_PASSWORD}   (Thyolo, English)")
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
