import os
import requests
import sqlite3
from datetime import datetime
from flask import Blueprint, request, jsonify
from dotenv import load_dotenv
from utils.shopify_utils import get_tokens

# Charger les variables d'environnement
load_dotenv()

# URL de l'API Google Analytics
GOOGLE_API_URL = "https://analyticsreporting.googleapis.com/v4/reports:batchGet"

# Création du blueprint Flask
api_google_bp = Blueprint('api_google', __name__)

# Récupérer les données Google Analytics
def fetch_google_analytics_data(shop, view_id, start_date, end_date):
    """ Récupère les données de Google Analytics """
    tokens = get_tokens(shop)
    access_token = tokens["google_token"] if tokens and tokens["google_token"] else None
    
    if not access_token:
        return {"error": "Token Google Analytics introuvable"}
    
    headers = {"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"}
    body = {
        "reportRequests": [
            {
                "viewId": view_id,
                "dateRanges": [{"startDate": start_date, "endDate": end_date}],
                "metrics": [
                    {"expression": "ga:sessions"},
                    {"expression": "ga:bounceRate"},
                    {"expression": "ga:productAddsToCart"},
                    {"expression": "ga:checkoutInitiated"},
                    {"expression": "ga:transactions"},
                    {"expression": "ga:avgSessionDuration"}
                ],
                "dimensions": [
                    {"name": "ga:source"}
                ]
            }
        ]
    }
    response = requests.post(GOOGLE_API_URL, json=body, headers=headers)
    return response.json()

# Sauvegarder les données Google Analytics dans la base de la boutique
def save_google_analytics_data(shop, view_id, start_date, end_date):
    """ Récupère et stocke les données Google Analytics """
    data = fetch_google_analytics_data(shop, view_id, start_date, end_date)
    if "error" in data:
        return data
    
    report = data.get("reports", [])[0]
    rows = report.get("data", {}).get("rows", [])
    
    db_path = f"databases/{shop}.db"
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for row in rows:
        values = row["metrics"][0]["values"]
        source = row["dimensions"][0]
        cursor.execute("""
            INSERT INTO google_analytics (date, sessions, bounce_rate, add_to_cart, checkout_started, transactions, avg_session_duration, source_traffic)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().strftime("%Y-%m-%d"),
            int(values[0]),  # Sessions
            float(values[1]),  # Bounce Rate
            int(values[2]),  # Add to Cart
            int(values[3]),  # Checkout Initiated
            int(values[4]),  # Transactions
            float(values[5]),  # Average Session Duration
            source  # Traffic Source
        ))
    
    conn.commit()
    conn.close()
    return {"message": "Données Google Analytics stockées dans la base de la boutique"}