from flask import Flask, jsonify, request
from flask_cors import CORS
from recipe import get_recipe_detail, get_public_recipes_filtered, get_filter_options
import os

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return "This is the 'CookingwithBB' home page."

@app.route("/recipes", methods=["GET"])
def list_recipes():
    q = request.args.get("q")
    cuisine = request.args.get("cuisine")
    diet = request.args.get("diet")
    difficulty = request.args.get("difficulty")
    tag = request.args.get("tag")

    recipes = get_public_recipes_filtered(
        q=q,
        cuisine=cuisine,
        diet=diet,
        difficulty=difficulty,
        tag=tag
    )
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

if __name__ == "__main__":
    app.run(debug=True)