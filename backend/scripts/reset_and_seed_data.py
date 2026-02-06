#!/usr/bin/env python3
"""
Script to reset all data and seed from 'приложение 3.docx'.

This script:
1. Deletes all students, specialties, SPO, specialty_templates, and operator users
2. Creates 21 SPO organizations from the document
3. Creates all specialty templates (unique specialties)
4. Assigns specialties to SPO according to the document

Usage:
    cd backend
    python -m scripts.reset_and_seed_data
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import SessionLocal, engine
from app.models import SPO, Specialty, SpecialtyTemplate, Student, User, UserRole


# Data from "приложение 3.docx" - 21 organizations with their specialties
# Format: (SPO name, [(specialty_code, specialty_name), ...])
DATA = [
    (
        "Государственное профессиональное образовательное учреждение Ростовской области «Азовский многопрофильный техникум»",
        [
            ("13.01.10", "Электромонтер по ремонту и обслуживанию электрооборудования (по отраслям)"),
            ("15.01.05", "Сварщик (ручной и частично механизированной сварки (наплавки)"),
        ]
    ),
    (
        "Государственное профессиональное образовательное учреждение Ростовской области «Белокалитвинский гуманитарно-индустриальный техникум»",
        [
            ("22.02.08", "Металлургическое производство (по видам производства)"),
        ]
    ),
    (
        "Государственное профессиональное образовательное учреждение Ростовской области «Вешенский педагогический колледж им. М.А. Шолохова»",
        [
            ("44.02.01", "Дошкольное образование"),
            ("44.02.02", "Преподавание в начальных классах"),
        ]
    ),
    (
        "Государственное профессиональное образовательное учреждение Ростовской области «Волгодонской медицинский колледж»",
        [
            ("34.02.01", "Сестринское дело"),
        ]
    ),
    (
        "Государственное профессиональное образовательное учреждение Ростовской области «Волгодонский техникум металлообработки и машиностроения»",
        [
            ("13.01.10", "Электромонтер по ремонту и обслуживанию электрооборудования (по отраслям)"),
            ("15.01.29", "Контролер качества в машиностроении"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Донской промышленно-технический колледж (ПУ № 8) имени Б.Н. Слюсаря»",
        [
            ("15.01.29", "Контролер качества в машиностроении"),
            ("24.02.01", "Производство летательных аппаратов"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Донской педагогический колледж»",
        [
            ("44.02.02", "Преподавание в начальных классах"),
            ("44.02.04", "Специальное дошкольное образование"),
            ("44.02.05", "Коррекционная педагогика в начальном образовании"),
            ("49.02.01", "Физическая культура"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Каменск-Шахтинский медицинский колледж»",
        [
            ("34.02.01", "Сестринское дело"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Константиновский педагогический колледж»",
        [
            ("44.02.01", "Дошкольное образование"),
            ("44.02.02", "Преподавание в начальных классах"),
            ("44.02.05", "Коррекционная педагогика в начальном образовании"),
            ("49.02.01", "Физическая культура"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Морозовский агропромышленный техникум»",
        [
            ("35.01.27", "Мастер сельскохозяйственного производства"),
            ("35.02.16", "Эксплуатация и ремонт сельскохозяйственной техники и оборудования"),
            ("49.02.01", "Физическая культура"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Новочеркасский медицинский колледж»",
        [
            ("34.02.01", "Сестринское дело"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Новочеркасский промышленно-гуманитарный колледж»",
        [
            ("15.01.05", "Сварщик (ручной и частично механизированной сварки (наплавки)"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Октябрьский аграрно-технологий техникум»",
        [
            ("35.01.27", "Мастер сельскохозяйственного производства"),
            ("35.02.16", "Эксплуатация и ремонт сельскохозяйственной техники и оборудования"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Ростовский-на-Дону автодорожный колледж»",
        [
            ("27.02.07", "Управление качеством продукции, процессов и услуг (по отраслям)"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Сальский аграрно-технический колледж»",
        [
            ("35.02.05", "Агрономия"),
            ("35.02.16", "Эксплуатация и ремонт сельскохозяйственной техники и оборудования"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Сальский медицинский колледж»",
        [
            ("34.02.01", "Сестринское дело"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Таганрогский авиационный колледж имени В.М. Петлякова»",
        [
            ("15.02.16", "Технология машиностроения"),
            ("27.02.07", "Управление качеством продукции, процессов и услуг (по отраслям)"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Таганрогский медицинский колледж»",
        [
            ("31.02.02", "Акушерское дело"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Таганрогский механический колледж»",
        [
            ("15.01.05", "Сварщик (ручной и частично механизированной сварки (наплавки)"),
            ("15.01.35", "Мастер слесарных работ"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Тарасовский многопрофильный техникум»",
        [
            ("35.01.27", "Мастер сельскохозяйственного производства"),
        ]
    ),
    (
        "Государственное бюджетное профессиональное образовательное учреждение Ростовской области «Шахтинский медицинский колледж им. Г.В. Кузнецовой»",
        [
            ("31.02.03", "Лабораторная диагностика"),
            ("34.02.01", "Сестринское дело"),
        ]
    ),
]


def reset_data(db):
    """Delete all data except admin users."""
    print("Deleting existing data...")

    # Delete in correct order due to foreign key constraints
    # 1. Students (references specialties)
    deleted_students = db.query(Student).delete()
    print(f"  Deleted {deleted_students} students")

    # 2. Specialties (references spo and specialty_templates)
    deleted_specialties = db.query(Specialty).delete()
    print(f"  Deleted {deleted_specialties} specialties")

    # 3. Specialty templates
    deleted_templates = db.query(SpecialtyTemplate).delete()
    print(f"  Deleted {deleted_templates} specialty templates")

    # 4. Operator users (references spo)
    deleted_operators = db.query(User).filter(User.role == UserRole.OPERATOR).delete()
    print(f"  Deleted {deleted_operators} operators")

    # 5. SPO
    deleted_spo = db.query(SPO).delete()
    print(f"  Deleted {deleted_spo} SPO organizations")

    db.commit()
    print("Data reset complete.\n")


def seed_data(db):
    """Seed data from приложение 3."""
    print("Seeding new data...")

    # First, collect all unique specialties to create templates
    unique_specialties = {}
    for spo_name, specialties in DATA:
        for code, name in specialties:
            if code not in unique_specialties:
                unique_specialties[code] = name

    # Create specialty templates
    print(f"\nCreating {len(unique_specialties)} specialty templates...")
    templates_map = {}
    for code, name in sorted(unique_specialties.items()):
        template = SpecialtyTemplate(code=code, name=name)
        db.add(template)
        db.flush()  # Get ID
        templates_map[code] = template
        print(f"  [{code}] {name}")

    # Create SPO and their specialties
    print(f"\nCreating {len(DATA)} SPO organizations with specialties...")
    total_specialties = 0

    for i, (spo_name, specialties) in enumerate(DATA, 1):
        # Create SPO
        spo = SPO(name=spo_name)
        db.add(spo)
        db.flush()  # Get ID

        # Create specialties for this SPO
        for code, name in specialties:
            template = templates_map[code]
            specialty = Specialty(
                spo_id=spo.id,
                template_id=template.id,
                name=name,
                code=code,
                quota=50  # Default quota
            )
            db.add(specialty)
            total_specialties += 1

        print(f"  {i}. {spo_name[:60]}... ({len(specialties)} specialties)")

    db.commit()
    print(f"\nSeeding complete!")
    print(f"  - Created {len(DATA)} SPO organizations")
    print(f"  - Created {len(unique_specialties)} specialty templates")
    print(f"  - Created {total_specialties} specialty assignments")


def main():
    """Main entry point."""
    print("=" * 60)
    print("SPO Quota System - Data Reset and Seed Script")
    print("Data source: приложение 3.docx")
    print("=" * 60)
    print()

    db = SessionLocal()
    try:
        reset_data(db)
        seed_data(db)
        print("\nDone!")
    except Exception as e:
        db.rollback()
        print(f"\nError: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
