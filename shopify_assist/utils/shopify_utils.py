import re
import sqlite3
import requests
import os
import logging
from datetime import datetime

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

# Validation du domaine Shopify
def is_valid_shop_domain(shop):
    pattern = r"^[a-zA-Z0-9][a-zA-Z0-9\-]*\.myshopify\.com$"
    valid = re.match(pattern, shop) is not None
    if not valid:
        logger.error(f"Le domaine Shopify '{shop}' n'est pas valide.")

# Stocker les tokens d'accès Shopify dans SQLite
def save_shopify_token(shop, shopify_token):
    """
    Stocke ou met à jour le token Shopify pour une boutique.
    """
    try:
        connection = sqlite3.connect("shopify_tokens.db")
        cursor = connection.cursor()

        # Création de la table pour stocker les tokens Shopify
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tokens (
                shop TEXT PRIMARY KEY,
                shopify_token TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        now = datetime.now().isoformat()  # Format ISO 8601
        cursor.execute("""
            INSERT INTO tokens (shop, shopify_token, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(shop) DO UPDATE SET
                shopify_token = excluded.shopify_token,
                updated_at = excluded.updated_at
        """, (shop, shopify_token, now, now))

        connection.commit()
        logger.info(f"Token Shopify sauvegardé/actualisé pour la boutique : {shop}")
    except sqlite3.Error as e:
        logger.error(f"Erreur SQLite : {e} pour la boutique : {shop}")
    finally:
        connection.close()

# Récupérer le token Shopify
def get_shopify_token(shop):
    """
    Récupère le token Shopify pour une boutique.
    """
    try:
        connection = sqlite3.connect("shopify_tokens.db")
        cursor = connection.cursor()
        cursor.execute("""
            SELECT shopify_token 
            FROM tokens 
            WHERE shop = ?
        """, (shop,))
        row = cursor.fetchone()
        logger.info(f"Token Shopify récupéré pour la boutique : {shop}")
        return row[0] if row else None
    except sqlite3.Error as e:
        logger.error(f"Erreur SQLite : {e} pour la boutique : {shop}")
        return None
    finally:
        connection.close()

# Exécuter une requête GraphQL vers Shopify
def execute_graphql_query(shop, query):
    """
    Exécute une requête GraphQL vers Shopify pour une boutique spécifique.
    """
    try:
        token = get_shopify_token(shop)
        
        if not token:
            logger.error(f"Token d'accès introuvable pour la boutique : {shop}")
            return {"error": "Token d'accès introuvable pour cette boutique."}

        url = f"https://{shop}/admin/api/2025-01/graphql.json"
        headers = {
            "X-Shopify-Access-Token": token,
            "Content-Type": "application/json"
        }
        response = requests.post(url, json={"query": query}, headers=headers)

        if response.status_code == 200:
            logger.info(f"Requête GraphQL réussie pour la boutique : {shop}")
            logger.debug(f"Requête GraphQL : {query}")
            return response.json()
        else:
            logger.error(f"Erreur lors de la requête GraphQL pour la boutique : {shop} - {response.status_code}")
            return {"error": "Erreur lors de l'exécution de la requête GraphQL.", "details": response.text}
    except requests.RequestException as e:
        logger.error(f"Erreur de requête : {e} pour la boutique : {shop}")
        return {"error": "Erreur de requête.", "details": str(e)}