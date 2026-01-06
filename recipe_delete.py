from connection_with_db import get_connection

def delete_recipe(recipe_id: int, owner_user_id: int) -> bool:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        DELETE FROM app.recipe
        WHERE id = ? AND owner_user_id = ?
    """, (recipe_id, owner_user_id))
    deleted = cur.rowcount > 0
    conn.commit()
    cur.close()
    conn.close()
    return deleted
