import os
from dotenv import load_dotenv
import sqlite3
import requests
from typing import Optional, Dict
from datetime import datetime

# Charger les variables d'environnement
load_dotenv()

class ShopifyGraphQL:
    def __init__(self):
        self.shop_name = os.getenv('SHOPIFY_SHOP_NAME')
        self.access_token = os.getenv('SHOPIFY_ACCESS_TOKEN')
        self.url = f"https://{self.shop_name}/admin/api/2024-01/graphql.json"
        self.headers = {
            'X-Shopify-Access-Token': self.access_token,
            'Content-Type': 'application/json'
        }

    def execute_query(self, query: str, variables: Dict = None) -> Optional[Dict]:
        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json={'query': query, 'variables': variables or {}}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Erreur lors de la requête : {str(e)}")
            return None

    def get_store_overview(self):
        query = """
        {
          shop {
            name
            email
            primaryDomain {
              url
            }
            plan {
              displayName
            }
          }
          products(first: 250) {
            edges {
              node {
                id
                title
                totalInventory
                priceRangeV2 {
                  minVariantPrice {
                    amount
                  }
                }
              }
            }
          }
          orders(first: 250) {
            edges {
              node {
                id
                totalPriceSet {
                  shopMoney {
                    amount
                  }
                }
                createdAt
              }
            }
          }
        }
        """
        return self.execute_query(query)

# Initialiser la base de données SQLite
def setup_database():
    connection = sqlite3.connect("shopify_data.db")
    cursor = connection.cursor()

    # Table pour les produits
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            product_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            total_inventory INTEGER,
            price REAL
        )
    """)

    # Table pour les commandes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            total_price REAL,
            created_at TEXT
        )
    """)

    connection.commit()
    connection.close()
    print("Base de données SQLite initialisée avec succès.")

# Sauvegarder les produits dans SQLite
def save_products_to_db(products):
    connection = sqlite3.connect("shopify_data.db")
    cursor = connection.cursor()

    for product in products:
        node = product['node']
        price = float(node['priceRangeV2']['minVariantPrice']['amount'])
        cursor.execute("""
            INSERT OR REPLACE INTO products (product_id, title, total_inventory, price)
            VALUES (?, ?, ?, ?)
        """, (
            node['id'],
            node['title'],
            node['totalInventory'],
            price
        ))

    connection.commit()
    connection.close()
    print("Produits sauvegardés dans la base de données SQLite.")

# Sauvegarder les commandes dans SQLite
def save_orders_to_db(orders):
    connection = sqlite3.connect("shopify_data.db")
    cursor = connection.cursor()

    for order in orders:
        node = order['node']
        total_price = float(node['totalPriceSet']['shopMoney']['amount'])
        cursor.execute("""
            INSERT OR REPLACE INTO orders (order_id, total_price, created_at)
            VALUES (?, ?, ?)
        """, (
            node['id'],
            total_price,
            node['createdAt']
        ))

    connection.commit()
    connection.close()
    print("Commandes sauvegardées dans la base de données SQLite.")

# Lire et afficher les produits depuis SQLite
def read_products_from_db():
    connection = sqlite3.connect("shopify_data_.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    connection.close()

    print("\n📦 Produits stockés :")
    for row in rows:
        print(f"- ID: {row[0]}, Titre: {row[1]}, Stock: {row[2]}, Prix: {row[3]}€")

# Lire et afficher les commandes depuis SQLite
def read_orders_from_db():
    connection = sqlite3.connect("shopify_data.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM orders")
    rows = cursor.fetchall()
    connection.close()

    print("\n🛍️ Commandes stockées :")
    for row in rows:
        print(f"- ID: {row[0]}, Total: {row[1]}€, Date: {row[2]}")

# Point d'entrée principal
if __name__ == "__main__":
    try:
        # Initialiser la base de données
        setup_database()

        # Récupérer les données Shopify
        client = ShopifyGraphQL()
        print("Récupération des données via GraphQL...")
        data = client.get_store_overview()

        if data and 'data' in data:
            # Sauvegarder les données dans SQLite
            save_products_to_db(data['data']['products']['edges'])
            save_orders_to_db(data['data']['orders']['edges'])

            # Lire et afficher les données stockées
            read_products_from_db()
            read_orders_from_db()

            print("\n✅ Données sauvegardées et vérifiées.")
        else:
            print("\n❌ Erreur lors de la récupération des données.")
    except Exception as e:
        print(f"\n❌ Erreur inattendue : {str(e)}")