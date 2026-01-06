from flask import Flask, request, jsonify, render_template
from flask_cors import CORS, cross_origin
import os
app = Flask(__name__)

@app.route('/')
def home():
    return "This is the 'CookingwithBB' home page."

@app.route("/bente", methods=["GET", "POST"])
def bente_route():
    result = bente.start()
    return result