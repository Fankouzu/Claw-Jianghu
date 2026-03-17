#!/usr/bin/env python
"""
Initialize database tables required for Evennia before migrations.
"""
import os
import psycopg

def main():
    url = os.environ.get('DATABASE_URL', '')
    if not url:
        print('DATABASE_URL not set')
        return

    conn = psycopg.connect(url)
    cur = conn.cursor()

    # Check if server_serverconfig exists
    cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name='server_serverconfig');")
    if not cur.fetchone()[0]:
        print('Creating server_serverconfig table...')
        cur.execute('''
            CREATE TABLE server_serverconfig (
                id SERIAL PRIMARY KEY,
                db_key VARCHAR(64) UNIQUE,
                db_value TEXT
            );
        ''')
        conn.commit()

        # Add migration records
        migrations = [
            ('server', '0001_initial'),
            ('server', '0002_auto_20190128_2311'),
            ('server', '0003_alter_serverconfig_id'),
        ]
        for app, name in migrations:
            cur.execute(
                'INSERT INTO django_migrations (app, name, applied) VALUES (%s, %s, NOW()) ON CONFLICT DO NOTHING;',
                (app, name)
            )
        conn.commit()
        print('Created server_serverconfig table and migration records')
    else:
        print('server_serverconfig table already exists')

    conn.close()

if __name__ == '__main__':
    main()