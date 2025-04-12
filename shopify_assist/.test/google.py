import os
import requests
from urllib.parse import urlencode
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from utils.shopify_utils import save_tokens, get_tokens  

# Charger les variables d'environnement
load_dotenv()

# Configuration OAuth Google
CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI")

# Scopes Google Analytics
SCOPES = "https://www.googleapis.com/auth/analytics.readonly"

# Création du blueprint Flask
google_bp = Blueprint('google', __name__)

# Fonction pour générer l'URL d'authentification Google
@google_bp.route("/auth/google")
def google_login():
    shop = request.args.get("shop")
    if not shop:
        return jsonify({"error": "Le paramètre 'shop' est requis"}), 400
    
    params = {
        "client_id": CLIENT_ID,
        "redirect_uri": f"{REDIRECT_URI}?shop={shop}",  # On ajoute le shop pour lier les tokens
        "response_type": "code",
        "scope": SCOPES,
        "access_type": "offline",
        "prompt": "consent"
    }
    auth_url = "https://accounts.google.com/o/oauth2/auth?" + urlencode(params)
    return jsonify({"auth_url": auth_url})

# Route pour gérer le callback OAuth
@google_bp.route("/auth/google/callback")
def google_callback():
    code = request.args.get("code")
    shop = request.args.get("shop")

    if not code or not shop:
        return jsonify({"error": "Code ou boutique manquant"}), 400
    
    # Échanger le code contre un token
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
        # Stocker le token Google dans la base centralisée avec Shopify
        save_tokens(shop, google_token=token_data.get("access_token"), google_refresh_token=token_data.get("refresh_token"))
        return jsonify({"message": "Authentification Google réussie !"})
    else:
        return jsonify({"error": "Échec de l'authentification", "details": token_data})

# Rafraîchir le token Google OAuth pour une boutique spécifique
def refresh_google_token(shop):
    tokens = get_tokens(shop)
    refresh_token = tokens["google_refresh_token"] if tokens and tokens["google_refresh_token"] else None
    
    if not refresh_token:
        return None
    
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    response = requests.post(token_url, data=data)
    new_token_data = response.json()
    
    if "access_token" in new_token_data:
        save_tokens(shop, google_token=new_token_data["access_token"])
        return new_token_data["access_token"]
    return None