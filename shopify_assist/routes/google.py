import os
import requests
import sqlite3
from datetime import datetime
from urllib.parse import urlencode
from flask import Blueprint, request, redirect, jsonify
from dotenv import load_dotenv
from utils.google_utils import sync_ga_metrics

# Charger les variables d'environnement
load_dotenv()

# Configuration OAuth
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")
TOKEN_DB = "shopify_tokens.db"
SCOPES = "https://www.googleapis.com/auth/analytics.readonly"

# Création du Blueprint Flask
google_bp = Blueprint('google', __name__)

# Générer le lien d'autorisation
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
    return jsonify({"auth_url": auth_url})

# Callback OAuth
@google_bp.route("/api/google/auth/google/callback")
def google_callback():
    code = request.args.get("code")
    shop = request.args.get("babaa94.myshopify.com")  # Facultatif mais utile si présent
    if not code:
        return jsonify({"error": "Code manquant"}), 400

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
        save_google_token(shop, token_data)
        return jsonify({"message": "Authentification Google réussie"})
    else:
        return jsonify({"error": "Échec de l'authentification", "details": token_data}), 400

# Stocker le token dans SQLite
def save_google_token(shop, token_data):
    conn = sqlite3.connect(TOKEN_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tokens (
            shop TEXT PRIMARY KEY,
            google_token TEXT,
            google_refresh_token TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    now = request.args.get("now") or request.form.get("now") or "auto"
    cursor.execute("""
        INSERT INTO tokens (shop, google_token, google_refresh_token, created_at, updated_at)
        VALUES (?, ?, ?, datetime('now'), datetime('now'))
        ON CONFLICT(shop) DO UPDATE SET
            google_token = excluded.google_token,
            google_refresh_token = excluded.google_refresh_token,
            updated_at = excluded.updated_at
    """, (
        shop or "default",  # À personnaliser si nécessaire
        token_data.get("access_token"),
        token_data.get("refresh_token")
    ))

    conn.commit()
    conn.close()

# Lancer la synchronisation manuellement
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
        return jsonify({"error": str(e)}), 500