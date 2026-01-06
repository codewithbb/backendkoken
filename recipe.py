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

def get_public_recipes_filtered(q=None, cuisine=None, diet=None, difficulty=None, tag=None):
    base_sql = """
        SELECT
            r.id,
            r.title,
            r.description,
            r.servings,
            r.prep_time_minutes,
            r.cook_time_minutes,
            r.cuisine,
            r.diet,
            r.difficulty
        FROM app.recipe r
        WHERE r.is_public = 1
    """

    params = []
    where_parts = []

    # Zoeken (q) in title/description (en evt voice_summary)
    if q:
        where_parts.append("(r.title LIKE ? OR r.description LIKE ? OR r.voice_summary LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like])

    # Exacte filters
    if cuisine:
        where_parts.append("r.cuisine = ?")
        params.append(cuisine)

    if diet:
        where_parts.append("r.diet = ?")
        params.append(diet)

    # difficulty (exact) – later kun je ook min/max doen
    if difficulty is not None:
        where_parts.append("r.difficulty = ?")
        params.append(int(difficulty))

    # Tag filter (1 tag) via EXISTS
    if tag:
        where_parts.append("""
            EXISTS (
              SELECT 1
              FROM app.recipe_tag rt
              JOIN app.tag t ON t.id = rt.tag_id
              WHERE rt.recipe_id = r.id AND t.name = ?
            )
        """)
        params.append(tag)

    # Voeg extra WHERE’s toe
    if where_parts:
        base_sql += " AND " + " AND ".join(where_parts)

    base_sql += " ORDER BY r.created_at DESC"

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(base_sql, params)

    columns = [c[0] for c in cursor.description]
    rows = [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn.close()
    return rows

def get_filter_options():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT cuisine FROM app.recipe WHERE is_public = 1 AND cuisine IS NOT NULL ORDER BY cuisine")
    cuisines = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT diet FROM app.recipe WHERE is_public = 1 AND diet IS NOT NULL ORDER BY diet")
    diets = [r[0] for r in cursor.fetchall()]

    cursor.execute("SELECT name FROM app.tag ORDER BY name")
    tags = [r[0] for r in cursor.fetchall()]

    conn.close()
    return {"cuisines": cuisines, "diets": diets, "tags": tags}