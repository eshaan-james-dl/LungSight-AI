import sqlite3
import uuid
import csv
import os
from werkzeug.security import generate_password_hash, check_password_hash
from google.adk.tools.tool_context import ToolContext


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(CURRENT_DIR, "Data", "CSV files")
os.makedirs(DATA_DIR, exist_ok=True)

DB_NAME = os.path.join(DATA_DIR, "users.db")
CSV_FILE = os.path.join(DATA_DIR, "user_details.csv")

def save_to_csv(full_name, gender, age, username, user_uuid):
    file_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["full_name", "gender", "age", "username", "user_uuid"])
        writer.writerow([full_name, gender, age, username, user_uuid])

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT,
            gender TEXT,
            age INTEGER,
            username TEXT UNIQUE,
            password TEXT,
            user_uuid TEXT
        )
    """)
    conn.commit()
    conn.close()

# ⬇⬇ NEW TOOL FOR THE ORCHESTRATOR ⬇⬇
def check_login_status(tool_context: ToolContext) -> dict:
    """Checks if the user is currently logged in."""
    is_logged_in = tool_context.state.get("logged_in", False)
    user_uuid = tool_context.state.get("uuid", "None")
    
    if is_logged_in:
        return {"status": "logged_in", "uuid": user_uuid, "message": "User is authenticated."}
    else:
        return {"status": "logged_out", "message": "User is NOT logged in."}


def signup_tool(full_name, gender, age, username, password, tool_context: ToolContext) -> dict:
    init_db()
    hashed_pw = generate_password_hash(password)
    user_uuid = str(uuid.uuid4())

    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("INSERT INTO users (full_name, gender, age, username, password, user_uuid) VALUES (?, ?, ?, ?, ?, ?)", 
                  (full_name, gender, age, username, hashed_pw, user_uuid))
        conn.commit()
        conn.close()

        save_to_csv(full_name, gender, age, username, user_uuid)

        # 🔥 Set Session State
        tool_context.state["logged_in"] = True
        tool_context.state["uuid"] = user_uuid

        return {"status": "success", "message": f"Account created. Logged in as {username}."}

    except sqlite3.IntegrityError:
        return {"status": "error", "message": "Username already exists."}


def login_tool(username, password, tool_context: ToolContext) -> dict:
    init_db()
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT password, user_uuid FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()

    if not user:
        return {"status": "error", "message": "Username not found."}

    stored_hash, user_uuid = user

    if check_password_hash(stored_hash, password):
        # 🔥 Set Session State
        tool_context.state["logged_in"] = True
        tool_context.state["uuid"] = user_uuid

        return {"status": "success", "message": "Login successful.", "uuid": user_uuid}

    return {"status": "error", "message": "Incorrect password."}