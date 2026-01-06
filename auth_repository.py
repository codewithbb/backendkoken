from connection_with_db import get_connection
from auth_utils import make_salt, hash_password_with_salt

def find_user_by_email(email: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT id, email, display_name, password_salt, password_hash_bin
        FROM app.[user]
        WHERE email = ?
    """, (email,))
    row = cur.fetchone()
    conn.close()
    return row  # None of tuple

def create_user(email: str, password: str, display_name: str):
    salt = make_salt()
    pw_hash = hash_password_with_salt(password, salt)

    conn = get_connection()
    cur = conn.cursor()

    # Email unique constraint bestaat al → als duplicate, krijg je error
    cur.execute("""
        INSERT INTO app.[user] (email, display_name, password_salt, password_hash_bin, password_hash)
        VALUES (?, ?, ?, ?, ?)
    """, (email, display_name, salt, pw_hash, "LEGACY_UNUSED"))

    conn.commit()

    # Return new user
    cur.execute("SELECT TOP 1 id, email, display_name FROM app.[user] WHERE email = ?", (email,))
    user = cur.fetchone()
    conn.close()
    return user

def verify_login(email: str, password: str):
    row = find_user_by_email(email)
    if row is None:
        return None

    user_id, db_email, display_name, db_salt, db_hash = row

    # Als je net migreert, kunnen salt/hash nog NULL zijn
    if db_salt is None or db_hash is None:
        return None

    expected = hash_password_with_salt(password, db_salt)
    if expected != db_hash:
        return None

    return {"id": user_id, "email": db_email, "display_name": display_name}
