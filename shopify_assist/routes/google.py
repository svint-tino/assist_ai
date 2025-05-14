import os
import requests
import logging
from datetime import datetime
from urllib.parse import urlencode
from flask import Blueprint, request, redirect, jsonify
from dotenv import load_dotenv
from utils.google_utils import sync_ga_metrics, save_google_tokens

# Charger les variables d'environnement
load_dotenv()

# === CONFIGURATION DU LOGGER ===
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

file_handler = logging.FileHandler(f"{log_dir}/database.log")
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(file_handler)

# Configuration OAuth
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
SCOPES = "https://www.googleapis.com/auth/analytics.readonly"

# Blueprint Flask
google_bp = Blueprint('google', __name__)

# 1. Générer le lien d'autorisation Google
@google_bp.route("/api/google/auth/google")
def google_login():
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = "https://accounts.google.com/o/oauth2/auth?" + urlencode(params)
    logger.info(f"URL d'autorisation Google générée : {auth_url}")
    return jsonify({"auth_url": auth_url})

# 2. Callback OAuth pour échanger le code contre les tokens
@google_bp.route("/api/google/auth/google/callback")
def google_callback():
    code = request.args.get("code")
    shop = request.args.get("shop") # Doit être fourni pour relier les tokens

    if not code or not shop:
        return jsonify({"error": "Code ou shop manquant"}), 400

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": REDIRECT_URI
    }

    response = requests.post(token_url, data=data)
    token_data = response.json()

    if "access_token" in token_data:
        save_google_tokens(shop, token_data.get("access_token"), token_data.get("refresh_token"))
        return jsonify({"message": f"Authentification réussie pour {shop}"}), 200
    else:
        logger.error(f"Échec de l'authentification pour {shop}: {token_data}")
        return jsonify({"error": "Échec de l'authentification", "details": token_data}), 400

# 3. Lancer la synchronisation GA
@google_bp.route("/api/google/sync", methods=["POST"])
def trigger_google_sync():
    data = request.json
    shop = data.get("shop")
    property_id = data.get("property_id")

    if not shop or not property_id:
        return jsonify({"error": "Paramètres manquants : 'shop' et 'property_id' requis."}), 400

    try:
        sync_ga_metrics(shop, property_id)
        return jsonify({"message": f"Données GA synchronisées pour {shop}."})
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation GA pour {shop}: {str(e)}")
        return jsonify({"error": str(e)}), 500