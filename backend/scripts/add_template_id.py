"""Add template_id column to specialties table."""
from sqlalchemy import text
from app.core.database import engine

with engine.begin() as conn:
    conn.execute(text(
        "ALTER TABLE specialties "
        "ADD COLUMN IF NOT EXISTS template_id INTEGER "
        "REFERENCES specialty_templates(id) ON DELETE CASCADE"
    ))
    conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_specialties_template_id "
        "ON specialties(template_id)"
    ))

print("Done: template_id column added")
