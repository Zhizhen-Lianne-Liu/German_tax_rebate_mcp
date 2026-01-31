#!/usr/bin/env python3
"""Reset database tables for Gemini embeddings (768 dimensions)"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'german_tax',
    'user': 'tax_user',
    'password': 'tax_password_local_only'
}

print("Connecting to PostgreSQL...")
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

print("Dropping old tables...")
cursor.execute('DROP TABLE IF EXISTS deductions CASCADE')
cursor.execute('DROP TABLE IF EXISTS forms CASCADE')
cursor.execute('DROP TABLE IF EXISTS tax_law CASCADE')
conn.commit()

print("✅ Old tables dropped. Run 'just ingest' to populate with Gemini embeddings.")

cursor.close()
conn.close()
