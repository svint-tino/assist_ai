import sqlite3
import os
import openai
from dotenv import load_dotenv

load_dotenv()
openai.api_key=os.environ.get("OPENAI_API_KEY")

# Fonction pour récupérer les produits depuis SQLite
def fetch_products_from_db():
    connection = sqlite3.connect("")
    cursor = connection.cursor()
    cursor.execute("SELECT title, total_inventory, price FROM products")
    rows = cursor.fetchall()
    connection.close()
    return rows

# Fonction pour récupérer les commandes depuis SQLite
def fetch_orders_from_db():
    connection = sqlite3.connect("shopify_data.db")
    cursor = connection.cursor()
    cursor.execute("SELECT total_price, created_at FROM orders")
    rows = cursor.fetchall()
    connection.close()
    return rows

# Formater les produits pour le prompt
def format_products_for_prompt(products):
    if not products:
        return "Aucun produit disponible."
    formatted = "Voici les produits disponibles :\n"
    for product in products:
        formatted += f"- {product[0]} (Stock : {product[1]}, Prix : {product[2]}€)\n"
    return formatted

# Formater les commandes pour le prompt
def format_orders_for_prompt(orders):
    if not orders:
        return "Aucune commande disponible."
    formatted = "Voici les dernières commandes :\n"
    for order in orders:
        formatted += f"- Commande du {order[1]} : Total = {order[0]}€\n"
    return formatted

# Fonction pour interroger le chatbot OpenAI
def ask_chatbot(question, products_data, orders_data):
    # Créer les messages pour le modèle
    messages = [
        {"role": "system", "content": "Vous êtes un assistant pour une boutique Shopify."},
        {"role": "system", "content": f"Données actuelles :\n\n{products_data}\n\n{orders_data}"},
        {"role": "user", "content": question}
    ]

    # Appeler OpenAI avec les messages formatés
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.1
    )
    return response.choices[0].message.content

# Script principal
if __name__ == "__main__":
    try:
        # Récupérer les données depuis SQLite
        products = fetch_products_from_db()
        orders = fetch_orders_from_db()

        # Formater les données pour le prompt
        products_data = format_products_for_prompt(products)
        orders_data = format_orders_for_prompt(orders)

        # Poser une question au chatbot
        print("\nDonnées Shopify prêtes à être utilisées.")
        question = input("Posez une question au chatbot : ")
        response = ask_chatbot(question, products_data, orders_data)

        # Afficher la réponse du chatbot
        print("\n🤖 Réponse du chatbot :")
        print(response)

    except Exception as e:
        print(f"Erreur : {str(e)}")