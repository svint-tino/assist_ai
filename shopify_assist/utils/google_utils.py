import sqlite3
import requests
import os
import logging
from dotenv import load_dotenv
from datetime import datetime
from utils.database import get_database_path, create_ga_metrics_table

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

TOKEN_DB = "shopify_tokens.db"

# Création ou mise à jour de la table `google_tokens`
def save_google_tokens(shop, access_token, refresh_token=None):
    try:
        conn = sqlite3.connect(TOKEN_DB)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS google_tokens (
                shop TEXT PRIMARY KEY,
                access_token TEXT,
                refresh_token TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        """)

        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO google_tokens (shop, access_token, refresh_token, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(shop) DO UPDATE SET
                access_token = excluded.access_token,
                refresh_token = COALESCE(excluded.refresh_token, google_tokens.refresh_token),
                updated_at = excluded.updated_at
        """, (shop, access_token, refresh_token, now, now))

        conn.commit()
        logger.info(f"Google tokens saved/updated for shop: {shop}")
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e} boutique: {shop}")
    finally:
        conn.close()

# Récupère l'access_token depuis google_tokens
def get_google_token(shop):
    try:
        conn = sqlite3.connect(TOKEN_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT access_token FROM google_tokens WHERE shop = ?", (shop,))
        row = cursor.fetchone()
        
        logger.info(f"Access token retrieved for shop: {shop}")
        return row[0] if row else None
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e} boutique: {shop}")
        return None
    finally:
        conn.close()

# Rafraîchit le token Google via refresh_token
def refresh_google_token(shop):
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        conn = sqlite3.connect(TOKEN_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT refresh_token FROM google_tokens WHERE shop = ?", (shop,))
        row = cursor.fetchone()
        conn.close()

        if not row or not row[0]:
            raise Exception("Aucun refresh_token disponible pour cette boutique.")

        refresh_token = row[0]

        response = requests.post("https://oauth2.googleapis.com/token", data={
            "client_id": client_id,
            "client_secret": client_secret,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        })

        data = response.json()
        if "access_token" in data:
            save_google_tokens(shop, data["access_token"], refresh_token)
            return data["access_token"]
        else:
            raise Exception(f"Échec du rafraîchissement : {data}")
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e} boutique: {shop}")
        raise

# Récupère les métriques GA4 et les stocke dans la base boutique
def sync_ga_metrics(shop, property_id):
    try:
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

        for attempt in range(2):
            response = requests.post(url, headers=headers, json=body)
            if response.status_code == 200:
                break
            elif attempt == 0 and response.status_code == 401:
                access_token = refresh_google_token(shop)
                headers["Authorization"] = f"Bearer {access_token}"
            else:
                raise Exception(f"Erreur API Google Analytics: {response.text}")

        rows = response.json().get("rows", [])
        if not rows:
            logger.info(f"Aucune donnée à synchroniser pour la boutique {shop}.")
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
                dims[0]["value"],  # date
                int(metrics[0]["value"]),
                int(metrics[1]["value"]),
                float(metrics[2]["value"]),
                float(metrics[3]["value"]),
                dims[1]["value"],  # source
                dims[2]["value"],  # medium
                datetime.now().isoformat()
            ))

        conn.commit()
        logger.info(f"Métriques GA4 synchronisées pour la boutique {shop}.")
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e} boutique: {shop}")
    finally:
        if conn in locals():
            conn.close()