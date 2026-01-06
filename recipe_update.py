from connection_with_db import get_connection

def update_recipe(recipe_id: int, owner_user_id: int, payload: dict) -> None:
    """
    Update recept + ingredients + steps + tags in 1 transaction.
    Simpele strategie: update basisinfo, delete children, re-insert.
    """

    title = (payload.get("title") or "").strip()
    description = (payload.get("description") or "").strip()

    if not title or not description:
        raise ValueError("title en description zijn verplicht")

    servings = int(payload.get("servings") or 1)
    prep = int(payload.get("prep_time_minutes") or 0)
    cook = int(payload.get("cook_time_minutes") or 0)

    cuisine = payload.get("cuisine")
    diet = payload.get("diet")
    difficulty = payload.get("difficulty")
    difficulty = int(difficulty) if difficulty not in (None, "",) else None

    is_public = bool(payload.get("is_public", True))
    voice_summary = payload.get("voice_summary")
    source_type = payload.get("source_type") or "manual"

    ingredients = payload.get("ingredients") or []
    steps = payload.get("steps") or []
    tags = payload.get("tags") or []

    if not isinstance(ingredients, list) or not isinstance(steps, list) or not isinstance(tags, list):
        raise ValueError("ingredients, steps, tags moeten arrays zijn")

    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("BEGIN TRANSACTION")

        # 1) Update recipe basisinfo (ownership nogmaals afdwingen in SQL)
        cur.execute("""
            UPDATE app.recipe
            SET
              title = ?,
              description = ?,
              servings = ?,
              prep_time_minutes = ?,
              cook_time_minutes = ?,
              cuisine = ?,
              diet = ?,
              difficulty = ?,
              is_public = ?,
              voice_summary = ?,
              source_type = ?,
              updated_at = SYSUTCDATETIME()
            WHERE id = ? AND owner_user_id = ?
        """, (
            title, description, servings, prep, cook,
            cuisine, diet, difficulty,
            1 if is_public else 0,
            voice_summary, source_type,
            recipe_id, owner_user_id
        ))

        if cur.rowcount == 0:
            raise PermissionError("Not allowed (not owner or recipe not found)")

        # 2) Replace ingredients/steps/tags
        cur.execute("DELETE FROM app.recipe_ingredient WHERE recipe_id = ?", (recipe_id,))
        cur.execute("DELETE FROM app.recipe_step WHERE recipe_id = ?", (recipe_id,))
        cur.execute("DELETE FROM app.recipe_tag WHERE recipe_id = ?", (recipe_id,))

        # Ingredients
        for idx, ing in enumerate(ingredients, start=1):
            if isinstance(ing, str):
                line = ing.strip()
                sort_order = idx
            else:
                line = (ing.get("line") or "").strip()
                sort_order = int(ing.get("sort_order") or idx)
            if not line:
                continue

            cur.execute("""
                INSERT INTO app.recipe_ingredient (recipe_id, line, sort_order)
                VALUES (?, ?, ?)
            """, (recipe_id, line, sort_order))

        # Steps
        for idx, st in enumerate(steps, start=1):
            if isinstance(st, str):
                instruction = st.strip()
                step_number = idx
                skill_level = None
                technique = None
                can_be_spoken = True
            else:
                instruction = (st.get("instruction") or "").strip()
                step_number = int(st.get("step_number") or idx)
                skill_level = st.get("skill_level")
                skill_level = int(skill_level) if skill_level not in (None, "") else None
                technique = st.get("technique")
                can_be_spoken = bool(st.get("can_be_spoken", True))

            if not instruction:
                continue

            cur.execute("""
                INSERT INTO app.recipe_step
                  (recipe_id, step_number, instruction, skill_level, technique, can_be_spoken)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (recipe_id, step_number, instruction, skill_level, technique, 1 if can_be_spoken else 0))

        # Tags (upsert + link)
        for t in tags:
            name = (t or "").strip().lower()
            if not name:
                continue

            cur.execute("SELECT id FROM app.tag WHERE name = ?", (name,))
            row = cur.fetchone()
            if row:
                tag_id = row[0]
            else:
                cur.execute("INSERT INTO app.tag (name) OUTPUT INSERTED.id VALUES (?)", (name,))
                tag_id = cur.fetchone()[0]

            cur.execute("""
                INSERT INTO app.recipe_tag (recipe_id, tag_id) VALUES (?, ?)
            """, (recipe_id, tag_id))

        cur.execute("COMMIT")
        conn.commit()

    except Exception:
        try:
            cur.execute("ROLLBACK")
            conn.commit()
        except Exception:
            pass
        raise
    finally:
        cur.close()
        conn.close()
