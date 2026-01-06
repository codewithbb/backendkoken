from flask import Flask, jsonify
from flask_cors import CORS
from recipe import get_all_public_recipes, get_recipe_detail
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "This is the 'CookingwithBB' home page."

@app.route("/recipes", methods=["GET", "POST"])
def list_recipes():
    recipes = get_all_public_recipes()
    return jsonify(recipes)

@app.get("/recipes/<int:recipe_id>")
def recipe_detail(recipe_id: int):
    recipe = get_recipe_detail(recipe_id)
    if recipe is None:
        return jsonify({"error": "Recipe not found"}), 404
    return jsonify(recipe)

if __name__ == "__main__":
    app.run(debug=True)