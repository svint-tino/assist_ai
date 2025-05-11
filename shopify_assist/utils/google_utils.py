import sqlite3
import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from utils.database import get_database_path, create_ga_metrics_table


load_dotenv()

# Récupère le token Google Analytics depuis la base locale
def get_google_token(shop):
    connection = sqlite3.connect("shopify_tokens.db")
    cursor = connection.cursor()
    cursor.execute("SELECT google_token FROM tokens WHERE shop = ?", (shop,))
    row = cursor.fetchone()
    connection.close()
    return row[0] if row else None

def refresh_google_token(shop):

    client_id = os.getenv("GOOGLE_CLIENT_ID")
    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

    connection = sqlite3.connect("shopify_tokens.db")
    cursor = connection.cursor()
    cursor.execute("""
        SELECT google_refresh_token FROM tokens WHERE shop = ?
    """, (shop,))
    row = cursor.fetchone()
    connection.close()

    if not row or not row[0]:
        raise Exception("Aucun refresh_token disponible pour ce shop.")

    refresh_token = row[0]

    response = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    })

    data = response.json()
    if "access_token" in data:
        # Met à jour le token dans la DB
        connection = sqlite3.connect("shopify_tokens.db")
        cursor = connection.cursor()
        cursor.execute("""
            UPDATE tokens
            SET google_token = ?, updated_at = datetime('now')
            WHERE shop = ?
        """, (data["access_token"], shop))
        connection.commit()
        connection.close()
        return data["access_token"]
    else:
        raise Exception(f"Échec du rafraîchissement : {data}")

# Synchronise les données GA4 pour une boutique et une propriété GA
def sync_ga_metrics(shop, property_id):
    access_token = get_google_token(shop)
    if not access_token:
        access_token = refresh_google_token(shop)

    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{property_id}:runReport"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    body = {
        "dimensions": [{"name": "date"}, {"name": "sessionSource"}, {"name": "sessionMedium"}],
        "metrics": [
            {"name": "sessions"},
            {"name": "users"},
            {"name": "bounceRate"},
            {"name": "averageSessionDuration"}
        ],
        "dateRanges": [{"startDate": "7daysAgo", "endDate": "today"}]
    }

    # Essayer une fois, et si token expiré → refresh + retry
    for attempt in range(2):
        response = requests.post(url, headers=headers, json=body)

        if response.status_code == 200:
            break
        elif attempt == 0 and response.status_code == 401:
            # Token expiré → on le rafraîchit et on réessaie une fois
            access_token = refresh_google_token(shop)
            headers["Authorization"] = f"Bearer {access_token}"
        else:
            raise Exception(f"Erreur API Google Analytics: {response.text}")

    rows = response.json().get("rows", [])
    if not rows:
        return

    create_ga_metrics_table(shop)
    db_path = get_database_path(shop)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    for row in rows:
        dims = row["dimensionValues"]
        metrics = row["metricValues"]

        cursor.execute("""
            INSERT INTO ga_metrics (
                date, sessions, users, bounce_rate,
                avg_session_duration, source, medium, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            dims[0]["value"],
            int(metrics[0]["value"]),
            int(metrics[1]["value"]),
            float(metrics[2]["value"]),
            float(metrics[3]["value"]),
            dims[1]["value"],
            dims[2]["value"],
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()

    