from flask import Flask, jsonify, request, session
from flask_cors import CORS
from functools import wraps
import os

from recipe import get_public_recipes_filtered, get_recipe_detail, get_filter_options
from auth_repository import create_user, verify_login, find_user_by_email
from recipe_create_repository import create_recipe

app = Flask(__name__)

# Sessions werken alleen goed met een secret key
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# Belangrijk voor cookies vanaf je frontend server (http://127.0.0.1:5500)
CORS(app, supports_credentials=True)


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return jsonify({"success": False, "error": "Not authenticated"}), 401
        return fn(*args, **kwargs)
    return wrapper


@app.get("/")
def home():
    return "CookingwithBB backend running"

# --- RECIPES ---
@app.get("/recipes")
def list_recipes():
    q = request.args.get("q")
    cuisine = request.args.get("cuisine")
    diet = request.args.get("diet")
    difficulty = request.args.get("difficulty")
    tag = request.args.get("tag")

    recipes = get_public_recipes_filtered(q=q, cuisine=cuisine, diet=diet, difficulty=difficulty, tag=tag)
    return jsonify(recipes)

@app.get("/recipes/<int:recipe_id>")
def recipe_detail(recipe_id: int):
    recipe = get_recipe_detail(recipe_id)
    if recipe is None:
        return jsonify({"error": "Recipe not found"}), 404
    return jsonify(recipe)

@app.get("/filters")
def filters():
    return jsonify(get_filter_options())

# --- AUTH (AR006) ---

@app.get("/auth/session")
def auth_session():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"logged_in": False, "user": None})

    # basis user info ophalen
    # (we gebruiken email lookup via id query hieronder; simpelste is een eigen query)
    # Voor nu: quick fetch
    # Tip: maak later find_user_by_id()
    return jsonify({"logged_in": True, "user": {"id": user_id, "email": session.get("email"), "display_name": session.get("display_name")}})

@app.post("/auth/register")
def register():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    display_name = (data.get("display_name") or "").strip()

    if not email or not password or not display_name:
        return jsonify({"success": False, "error": "email, password en display_name zijn verplicht"}), 400

    if len(password) < 8:
        return jsonify({"success": False, "error": "Wachtwoord moet minimaal 8 tekens zijn"}), 400

    # Bestaat email al?
    if find_user_by_email(email) is not None:
        return jsonify({"success": False, "error": "Dit emailadres is al in gebruik"}), 409

    user = create_user(email=email, password=password, display_name=display_name)

    # Auto-login na registreren (handig UX)
    session["user_id"] = user[0]
    session["email"] = user[1]
    session["display_name"] = user[2]

    return jsonify({"success": True, "user": {"id": user[0], "email": user[1], "display_name": user[2]}}), 201

@app.post("/auth/login")
def login():
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"success": False, "error": "email en password zijn verplicht"}), 400

    user = verify_login(email=email, password=password)
    if user is None:
        return jsonify({"success": False, "error": "Ongeldige email of wachtwoord"}), 401

    session["user_id"] = user["id"]
    session["email"] = user["email"]
    session["display_name"] = user["display_name"]

    return jsonify({"success": True, "user": user})

@app.post("/auth/logout")
def logout():
    session.clear()
    return jsonify({"success": True})

@app.post("/recipes")
@login_required
def create_recipe_route():
    payload = request.get_json(silent=True) or {}
    owner_user_id = int(session["user_id"])

    try:
        recipe_id = create_recipe(owner_user_id, payload)
        return jsonify({"success": True, "id": recipe_id}), 201
    except ValueError as ve:
        return jsonify({"success": False, "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {e}"}), 500

if __name__ == "__main__":
    app.run(debug=True)
