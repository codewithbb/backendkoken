from connection_with_db import get_connection

def is_owner(recipe_id: int, user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT owner_user_id FROM app.recipe WHERE id = ?", (recipe_id,))
    row = cur.fetchone()
    conn.close()
    return (row is not None) and (row[0] == user_id)
