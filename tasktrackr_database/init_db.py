#!/usr/bin/env python3
"""Initialize SQLite database for tasktrackr_database

This script creates (or updates, if missing columns/tables) the database schema for TaskTrackr.
- Adds/extends 'users' table with password_hash for authentication.
- Adds 'tasks' table (id, user_id, title, description, due_date, completed).
- Seeds basic data.
"""

import sqlite3
import os

DB_NAME = "myapp.db"
DB_USER = "kaviasqlite"  # Not used for SQLite, but kept for consistency
DB_PASSWORD = "kaviadefaultpassword"  # Not used for SQLite, but kept for consistency
DB_PORT = "5000"  # Not used for SQLite, but kept for consistency

print("Starting SQLite setup...")

# Check if database already exists
db_exists = os.path.exists(DB_NAME)
if db_exists:
    print(f"SQLite database already exists at {DB_NAME}")
    # Verify it's accessible
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute("SELECT 1")
        conn.close()
        print("Database is accessible and working.")
    except Exception as e:
        print(f"Warning: Database exists but may be corrupted: {e}")
else:
    print("Creating new SQLite database...")

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Create app_info table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# 1. USERS table: Ensure table exists, and add password_hash if needed

# Check if users table exists (for idempotency)
cursor.execute("""
    SELECT name FROM sqlite_master WHERE type='table' AND name='users'
""")
users_exists = cursor.fetchone() is not None

if not users_exists:
    # Create fresh users table
    cursor.execute("""
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("Created users table.")
else:
    # Add password_hash column if it does not exist
    cursor.execute("PRAGMA table_info(users)")
    user_cols = [row[1] for row in cursor.fetchall()]
    if 'password_hash' not in user_cols:
        cursor.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        print("Added password_hash column to users table.")

# 2. TASKS table: Create if not exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        completed INTEGER DEFAULT 0,  -- 0 = not complete, 1 = complete
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
""")
print("Ensured tasks table exists.")

# 3. Insert or update initial seed data
# Insert App Info
cursor.execute("INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)", 
               ("project_name", "tasktrackr_database"))
cursor.execute("INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)", 
               ("version", "0.1.0"))
cursor.execute("INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)", 
               ("author", "John Doe"))
cursor.execute("INSERT OR REPLACE INTO app_info (key, value) VALUES (?, ?)", 
               ("description", ""))

# If users table is empty, insert a sample user
cursor.execute("SELECT COUNT(*) FROM users")
u_ct = cursor.fetchone()[0]
if u_ct == 0:
    import hashlib
    # Simple password hash for demonstration (DO NOT use in prod)
    plaintext_pw = "testpassword"
    hashval = hashlib.sha256(plaintext_pw.encode("utf-8")).hexdigest()
    cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
                   ("demo", "demo@example.com", hashval))
    print("Seeded initial user 'demo/demo@example.com' (password: testpassword)")

# If tasks table is empty, insert a sample task for demo user
cursor.execute("SELECT COUNT(*) FROM tasks")
t_ct = cursor.fetchone()[0]
if t_ct == 0:
    # Find demo user id
    cursor.execute("SELECT id FROM users WHERE username=?", ("demo",))
    demo_user = cursor.fetchone()
    if demo_user:
        user_id = demo_user[0]
        cursor.execute(
            "INSERT INTO tasks (user_id, title, description, due_date, completed) VALUES (?, ?, ?, ?, ?)",
            (user_id, "Welcome Task", "This is your first task!", "2024-07-04", 0)
        )
        print("Seeded initial task for demo user.")

conn.commit()

# Get database statistics
cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
table_count = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM app_info")
record_count = cursor.fetchone()[0]

conn.close()

# Save connection information to a file
current_dir = os.getcwd()
connection_string = f"sqlite:///{current_dir}/{DB_NAME}"

try:
    with open("db_connection.txt", "w") as f:
        f.write(f"# SQLite connection methods:\n")
        f.write(f"# Python: sqlite3.connect('{DB_NAME}')\n")
        f.write(f"# Connection string: {connection_string}\n")
        f.write(f"# File path: {current_dir}/{DB_NAME}\n")
    print("Connection information saved to db_connection.txt")
except Exception as e:
    print(f"Warning: Could not save connection info: {e}")

# Create environment variables file for Node.js viewer
db_path = os.path.abspath(DB_NAME)

# Ensure db_visualizer directory exists
if not os.path.exists("db_visualizer"):
    os.makedirs("db_visualizer", exist_ok=True)
    print("Created db_visualizer directory")

try:
    with open("db_visualizer/sqlite.env", "w") as f:
        f.write(f"export SQLITE_DB=\"{db_path}\"\n")
    print(f"Environment variables saved to db_visualizer/sqlite.env")
except Exception as e:
    print(f"Warning: Could not save environment variables: {e}")

print("\nSQLite setup complete!")
print(f"Database: {DB_NAME}")
print(f"Location: {current_dir}/{DB_NAME}")
print("")

print("To use with Node.js viewer, run: source db_visualizer/sqlite.env")

print("\nTo connect to the database, use one of the following methods:")
print(f"1. Python: sqlite3.connect('{DB_NAME}')")
print(f"2. Connection string: {connection_string}")
print(f"3. Direct file access: {current_dir}/{DB_NAME}")
print("")

print("Database statistics:")
print(f"  Tables: {table_count}")
print(f"  App info records: {record_count}")

# If sqlite3 CLI is available, show how to use it
try:
    import subprocess
    result = subprocess.run(['which', 'sqlite3'], capture_output=True, text=True)
    if result.returncode == 0:
        print("")
        print("SQLite CLI is available. You can also use:")
        print(f"  sqlite3 {DB_NAME}")
except:
    pass

print("\nScript completed successfully.")
