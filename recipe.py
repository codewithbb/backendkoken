from connection_with_db import get_connection

def get_all_public_recipes():
    sql = """
        SELECT
            id,
            title,
            description,
            servings,
            prep_time_minutes,
            cook_time_minutes,
            cuisine,
            diet,
            difficulty
        FROM app.recipe
        WHERE is_public = 1
        ORDER BY created_at DESC
    """

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(sql)

    columns = [column[0] for column in cursor.description]
    recipes = []

    for row in cursor.fetchall():
        recipes.append(dict(zip(columns, row)))

    conn.close()
    return recipes


def get_recipe_detail(recipe_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    # 1) Recept basis
    cursor.execute("""
        SELECT
            id, owner_user_id, title, description,
            servings, prep_time_minutes, cook_time_minutes,
            cuisine, diet, difficulty, is_public,
            voice_summary, source_type,
            created_at, updated_at
        FROM app.recipe
        WHERE id = ? AND is_public = 1
    """, (recipe_id,))
    row = cursor.fetchone()

    if row is None:
        conn.close()
        return None

    columns = [c[0] for c in cursor.description]
    recipe = dict(zip(columns, row))

    # 2) Ingrediënten
    cursor.execute("""
        SELECT line, sort_order
        FROM app.recipe_ingredient
        WHERE recipe_id = ?
        ORDER BY sort_order
    """, (recipe_id,))
    recipe["ingredients"] = [
        {"line": r[0], "sort_order": r[1]}
        for r in cursor.fetchall()
    ]

    # 3) Stappen
    cursor.execute("""
        SELECT step_number, instruction, skill_level, technique, can_be_spoken
        FROM app.recipe_step
        WHERE recipe_id = ?
        ORDER BY step_number
    """, (recipe_id,))
    recipe["steps"] = [
        {
            "step_number": r[0],
            "instruction": r[1],
            "skill_level": r[2],
            "technique": r[3],
            "can_be_spoken": bool(r[4]),
        }
        for r in cursor.fetchall()
    ]

    conn.close()
    return recipe

