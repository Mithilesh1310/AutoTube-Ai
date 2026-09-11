import sqlite3
import psycopg2

def migrate():
    sqlite_conn = sqlite3.connect('autotube.db')
    sqlite_cur = sqlite_conn.cursor()

    pg_conn = psycopg2.connect(host='127.0.0.1', port=5432, user='postgres', password='postgres', dbname='autotube')
    pg_cur = pg_conn.cursor()

    tables = [
        'users',
        'characters',
        'settings',
        'youtube_channels',
        'channel_automation_profiles',
        'scripts',
        'videos',
        'jobs',
        'job_logs',
        'animation_assets',
    ]

    for t in tables:
        try:
            sqlite_cur.execute(f"SELECT * FROM {t}")
            rows = sqlite_cur.fetchall()
            if not rows:
                print(f"Table {t} has 0 rows.")
                continue
            col_names = [d[0] for d in sqlite_cur.description]
            
            # Check column types in PG
            pg_cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = %s;
            """, (t,))
            pg_cols_info = {r[0]: r[1] for r in pg_cur.fetchall()}
            
            valid_indices = [i for i, c in enumerate(col_names) if c in pg_cols_info]
            valid_cols = [col_names[i] for i in valid_indices]
            
            placeholders = ', '.join(['%s'] * len(valid_cols))
            cols_str = ', '.join(f'"{c}"' for c in valid_cols)
            
            query = f'INSERT INTO "{t}" ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;'
            
            for r in rows:
                filtered_row = []
                for i in valid_indices:
                    val = r[i]
                    col = col_names[i]
                    dtype = pg_cols_info.get(col)
                    # Convert integer 0/1 to boolean if PG expects boolean
                    if dtype == 'boolean' and val is not None:
                        val = bool(val)
                    filtered_row.append(val)
                pg_cur.execute(query, filtered_row)
            pg_conn.commit()
            print(f"Successfully migrated {len(rows)} rows into {t}!")
        except Exception as e:
            print(f"Error migrating {t}: {e}")
            pg_conn.rollback()

    # Reset sequences for auto-increment IDs in postgres
    for t in tables:
        try:
            pg_cur.execute(f"SELECT setval(pg_get_serial_sequence('{t}', 'id'), coalesce(max(id), 1)) FROM \"{t}\";")
            pg_conn.commit()
        except Exception:
            pg_conn.rollback()

    pg_cur.close()
    pg_conn.close()
    sqlite_cur.close()
    sqlite_conn.close()
    print("ALL DATA MIGRATION COMPLETE!")

if __name__ == '__main__':
    migrate()
