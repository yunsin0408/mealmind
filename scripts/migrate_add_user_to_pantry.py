"""
Migration helper: add `user_id` column to `pantry_items` table for SQLite.
- It checks whether `user_id` exists and will do nothing if already present.
- For SQLite it recreates the table with the new column, copies data, and preserves existing rows (user_id will be NULL).
- Backup your `instance/mealmind.db` before running.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'mealmind.db')

def column_exists(conn, table, column):
    cur = conn.execute(f"PRAGMA table_info({table});")
    cols = [r[1] for r in cur.fetchall()]
    return column in cols


def main():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    try:
        if column_exists(conn, 'pantry_items', 'user_id'):
            print('Column `user_id` already exists on pantry_items — nothing to do.')
            return

        print('Starting migration: adding user_id to pantry_items...')
        cur = conn.cursor()
        # Start transaction
        cur.execute('BEGIN')
        # Create new table with user_id column
        cur.execute('''
        CREATE TABLE pantry_items_new (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            user_id INTEGER,
            quantity REAL,
            unit TEXT,
            expiration_date DATE
        );
        ''')
        # Copy data from old table into new (user_id will be NULL)
        cur.execute('''
        INSERT INTO pantry_items_new (id, name, category_id, quantity, unit, expiration_date)
        SELECT id, name, category_id, quantity, unit, expiration_date FROM pantry_items;
        ''')
        # Drop old table
        cur.execute('DROP TABLE pantry_items;')
        # Rename new table
        cur.execute('ALTER TABLE pantry_items_new RENAME TO pantry_items;')
        conn.commit()
        print('Migration completed successfully. user_id column added (existing rows have NULL).')
    except Exception as e:
        conn.rollback()
        print('Migration failed:', e)
    finally:
        conn.close()

if __name__ == '__main__':
    main()
