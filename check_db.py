import os
import psycopg

url = os.environ.get('DATABASE_URL', '')
print('Checking database...')
conn = psycopg.connect(url)
cur = conn.cursor()

# Get tables
cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name;")
tables = cur.fetchall()
print(f'Found {len(tables)} tables:')
for t in tables[:30]:
    print(f'  - {t[0]}')

# Check if django_migrations table exists
cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name='django_migrations');")
has_migrations = cur.fetchone()[0]
print(f'\ndjango_migrations table exists: {has_migrations}')

if has_migrations:
    cur.execute("SELECT app, name FROM django_migrations ORDER BY id LIMIT 20;")
    migrations = cur.fetchall()
    print('\nRecent migrations:')
    for m in migrations:
        print(f'  - {m[0]}.{m[1]}')

conn.close()