import sqlite3
from flask import current_app, g
import os

def get_db():
    """Get a database connection."""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None):
    """Schließt die Datenbankverbindung."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialisiere die Datenbank, wenn sie noch nicht existiert."""
    db = get_db()
    sql_path = os.path.join(current_app.instance_path, 'Sql', 'create_tables.sql')
    
    try:
        with current_app.open_resource(sql_path) as f:
            db.executescript(f.read().decode('utf8'))
        print("Database initialized.")
    except Exception as e:
        print(f"Error initializing database: {e}")

def init_app(app):
    """Registriere die Datenbankfunktionen und initialisiere die DB bei Bedarf."""
    app.teardown_appcontext(close_db)

    # Initialisiere die Datenbank nur, wenn sie noch nicht existiert
    if not os.path.exists(app.config['DATABASE']):
        with app.app_context():
            init_db()
            print("Database initialized for the first time.")

