from flask import Flask
from routes.shopify import shopify_bp
from routes.graphql import graphql_bp
from routes.assistant import assistant_bp
from routes.google import google_bp
from flask import render_template
from dotenv import load_dotenv
from flask_cors import CORS
import os

# Charger les variables d'environnement depuis .env
load_dotenv()

# Initialiser l'application Flask
app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

# Enregistrer les Blueprints pour organiser les routes
app.register_blueprint(shopify_bp, url_prefix="/api/shopify")
app.register_blueprint(graphql_bp, url_prefix="/api/shopify/graphql")
app.register_blueprint(assistant_bp, url_prefix="/api/assistant")
app.register_blueprint(google_bp)

# Configurations supplémentaires
@app.route('/')
def index():
    return "Ask with KOOC !"

@app.route("/test")
def test_assistant():
    return render_template("test_assistant.html")

# Point d'entrée principal
if __name__ == "__main__":
    app.run(port=4000, debug=True)