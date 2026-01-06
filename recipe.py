from connection_with_db import get_connection

def get_all_public_recipes():
    sql = """
        SELECT
            id,
            title,
            description,
            image_url,
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
    recipes = [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn.close()
    return recipes


def get_recipe_detail(recipe_id: int, current_user_id: int | None = None):
    conn = get_connection()
    cursor = conn.cursor()

    if current_user_id is None:
        cursor.execute("""
            SELECT
                id, owner_user_id, title, description,
                image_url,
                servings, prep_time_minutes, cook_time_minutes,
                cuisine, diet, difficulty, is_public,
                voice_summary, source_type,
                created_at, updated_at
            FROM app.recipe
            WHERE id = ? AND is_public = 1
        """, (recipe_id,))
    else:
        cursor.execute("""
            SELECT
                id, owner_user_id, title, description,
                image_url,
                servings, prep_time_minutes, cook_time_minutes,
                cuisine, diet, difficulty, is_public,
                voice_summary, source_type,
                created_at, updated_at
            FROM app.recipe
            WHERE id = ? AND (is_public = 1 OR owner_user_id = ?)
        """, (recipe_id, current_user_id))

    row = cursor.fetchone()
    if row is None:
        conn.close()
        return None

    columns = [c[0] for c in cursor.description]
    recipe = dict(zip(columns, row))

    cursor.execute("""
        SELECT line, sort_order
        FROM app.recipe_ingredient
        WHERE recipe_id = ?
        ORDER BY sort_order
    """, (recipe_id,))
    recipe["ingredients"] = [{"line": r[0], "sort_order": r[1]} for r in cursor.fetchall()]

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

    # ✅ tags (handig voor edit)
    cursor.execute("""
        SELECT t.name
        FROM app.recipe_tag rt
        JOIN app.tag t ON t.id = rt.tag_id
        WHERE rt.recipe_id = ?
        ORDER BY t.name
    """, (recipe_id,))
    recipe["tags"] = [r[0] for r in cursor.fetchall()]

    conn.close()
    return recipe


def get_public_recipes_filtered(q=None, cuisine=None, diet=None, difficulty=None, tag=None):
    base_sql = """
        SELECT
            r.id,
            r.title,
            r.description,
            r.image_url,
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

    if q:
        where_parts.append("(r.title LIKE ? OR r.description LIKE ? OR r.voice_summary LIKE ?)")
        like = f"%{q}%"
        params.extend([like, like, like])

    if cuisine:
        where_parts.append("r.cuisine = ?")
        params.append(cuisine)

    if diet:
        where_parts.append("r.diet = ?")
        params.append(diet)

    if difficulty not in (None, ""):
        where_parts.append("r.difficulty = ?")
        params.append(int(difficulty))

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


def get_my_recipes(owner_user_id: int):
    sql = """
        SELECT
            id,
            title,
            description,
            image_url,
            servings,
            prep_time_minutes,
            cook_time_minutes,
            cuisine,
            diet,
            difficulty,
            is_public,
            created_at,
            updated_at
        FROM app.recipe
        WHERE owner_user_id = ?
        ORDER BY updated_at DESC, created_at DESC
    """

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, (owner_user_id,))
    cols = [c[0] for c in cur.description]
    rows = [dict(zip(cols, r)) for r in cur.fetchall()]
    conn.close()
    return rows
