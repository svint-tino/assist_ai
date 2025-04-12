import re
import sqlite3
import requests
from datetime import datetime

# Validation du domaine Shopify
def is_valid_shop_domain(shop):
    pattern = r"^[a-zA-Z0-9][a-zA-Z0-9\-]*\.myshopify\.com$"
    return re.match(pattern, shop) is not None

# Stocker les tokens d'accès Shopify dans SQLite
def save_shopify_token(shop, shopify_token):
    """
    Stocke ou met à jour le token Shopify pour une boutique.
    """
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
    connection.close()

# Récupérer le token Shopify
def get_shopify_token(shop):
    """
    Récupère le token Shopify pour une boutique.
    """
    connection = sqlite3.connect("shopify_tokens.db")
    cursor = connection.cursor()
    cursor.execute("""
        SELECT shopify_token 
        FROM tokens 
        WHERE shop = ?
    """, (shop,))
    token = cursor.fetchone()
    connection.close()

    return token[0] if token else None

# Exécuter une requête GraphQL vers Shopify
def execute_graphql_query(shop, query):
    """
    Exécute une requête GraphQL vers Shopify pour une boutique spécifique.
    """
    token = get_shopify_token(shop)
    
    if not token:
        return {"error": "Token d'accès introuvable pour cette boutique."}

    url = f"https://{shop}/admin/api/2025-01/graphql.json"
    headers = {
        "X-Shopify-Access-Token": token,
        "Content-Type": "application/json"
    }
    response = requests.post(url, json={"query": query}, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Erreur lors de l'exécution de la requête GraphQL.", "details": response.text}