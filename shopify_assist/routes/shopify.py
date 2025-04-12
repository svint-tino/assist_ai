from flask import Blueprint, request, redirect, jsonify, session
import os
import requests
import secrets
from utils.shopify_utils import is_valid_shop_domain, save_shopify_token

# Initialiser le Blueprint pour Shopify
shopify_bp = Blueprint('shopify', __name__)

# Charger les variables d'environnement
SHOPIFY_ID = os.getenv("SHOPIFY_ID")
SHOPIFY_SECRET = os.getenv("SHOPIFY_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI", "http://localhost:4000/api/shopify/redirect")

# Route pour générer l'URL d'autorisation Shopify
@shopify_bp.route('/authorize', methods=['GET'])
def authorize():
    shop = request.args.get('shop')
    if not shop or not is_valid_shop_domain(shop):
        return jsonify({"error": "Paramètre 'shop' invalide"}), 400

    # Générer un état unique pour la prévention CSRF
    state = secrets.token_hex(16)
    session['state'] = state

    # Construire l'URL d'autorisation Shopify
    auth_url = (
        f"https://{shop}/admin/oauth/authorize?"
        f"client_id={SHOPIFY_ID}&"
        f"scope=read_products,read_orders,read_customers,"
        f"read_inventory,read_discounts,read_price_rules,"
        f"read_analytics,read_fulfillments,read_inventory,read_themes&"
        f"redirect_uri={REDIRECT_URI}&"
        f"state={state}"
    )
    return redirect(auth_url)

# Route pour gérer la redirection après l'autorisation
@shopify_bp.route('/redirect', methods=['GET'])
def shopify_redirect():
    code = request.args.get('code')
    shop = request.args.get('shop')
    state = request.args.get('state')

    # Vérification des paramètres reçus
    if not code or not shop or not state or state != session.get('state'):
        return jsonify({"error": "Paramètres invalides ou attaque CSRF détectée."}), 400

    if not is_valid_shop_domain(shop):
        return jsonify({"error": "Domaine Shopify invalide."}), 400

    # Échanger le code d'autorisation contre un token d'accès
    token_url = f"https://{shop}/admin/oauth/access_token"
    payload = {
        "client_id": SHOPIFY_ID,
        "client_secret": SHOPIFY_SECRET,
        "code": code
    }
    
    try:
        response = requests.post(token_url, json=payload)
        response.raise_for_status()
        access_token = response.json().get("access_token")

        # Stocker le token d'accès Shopify
        save_shopify_token(shop=shop, shopify_token=access_token)

        return jsonify({"message": "Autorisation Shopify réussie", "access_token": access_token})

    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": "Échec de la récupération du token d'accès",
            "details": str(e),
            "status_code": response.status_code if response else "N/A"
        }), 400