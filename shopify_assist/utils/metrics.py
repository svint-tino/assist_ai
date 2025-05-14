import sqlite3
import os
import logging
from utils.database import get_database_path
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict

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

# Ajout de colonnes analytiques à la table products si besoin
def add_product_metrics_columns(shop):
    db_path = get_database_path(shop)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(products);")
    existing_columns = [col[1] for col in cursor.fetchall()]

    fields = {
        "revenue": "REAL DEFAULT 0.0",
        "quantity_sold": "INTEGER DEFAULT 0",
        "margin": "REAL DEFAULT 0.0",
        "growth_rate": "REAL DEFAULT 0.0"
    }

    for column, definition in fields.items():
        if column not in existing_columns:
            cursor.execute(f"ALTER TABLE products ADD COLUMN {column} {definition}")
            logger.info(f"[{shop}] Colonne '{column}' ajoutée à la table products.")

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_order_items_unique ON order_items(order_id, product_id);")
    conn.commit()
    conn.close()


# Fonction principale de calcul des métriques
def calculate_product_metrics(shop):
    logger.info(f"[{shop}] Début du calcul des métriques produits")

    db_path = get_database_path(shop)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    today = datetime.now().strftime('%Y-%m-%d')
    period_type = "daily"
    updated_at = datetime.now().isoformat()
    
    # Ajout des colonnes analytiques si elles n'existent pas
    add_product_metrics_columns(shop)

    
    try:
        # Calcul des données produits
        cursor.execute("""
            SELECT 
                oi.product_id, 
                SUM(oi.quantity) as qty_sold, 
                SUM(oi.quantity * oi.price) as revenue,
                p.cost
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            JOIN products p ON oi.product_id = p.id
            GROUP BY oi.product_id
        """)

        # Mise à jour des produits avec les données calculées
        for product_id, qty, revenue, cost in cursor.fetchall():
            cost = cost or 0.0
            margin_total = 0.0 if not cost else revenue - (cost * qty)

            cursor.execute("""
                UPDATE products
                SET quantity_sold = ?, revenue = ?, margin = ?
                WHERE id = ?
            """, (qty, revenue, margin_total, product_id))
        logger.info(f"[{shop}] Mises à jour des produits effectuées")

        # Calcul du taux de croissance journalier
        cursor.execute("""
            SELECT 
                oi.product_id, 
                DATE(o.created_at) AS day,
                SUM(oi.quantity * oi.price) AS revenue
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            GROUP BY oi.product_id, day
        """)
        data = defaultdict(dict)
        for product_id, day, rev in cursor.fetchall():
            data[product_id][day] = rev

        today = datetime.now().strftime('%Y-%m-%d')
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

        # Mise à jour du taux de croissance
        for product_id, days in data.items():
            rev_today = days.get(today, 0.0)
            rev_yesterday = days.get(yesterday, 0.0)
            growth = ((rev_today - rev_yesterday) / rev_yesterday * 100) if rev_yesterday else 0.0

            cursor.execute("""
                UPDATE products
                SET growth_rate = ?
                WHERE id = ?
            """, (growth, product_id))

        # Création de la table analytics
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analytics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                period TEXT,
                period_type TEXT DEFAULT 'daily',
                total_revenue REAL DEFAULT 0.0,
                total_orders INTEGER DEFAULT 0,
                average_order_value REAL DEFAULT 0.0,
                cltv REAL DEFAULT 0.0,
                updated_at TEXT
            )
        """)
        logger.info(f"[{shop}] Table analytics prête")

        # Synchronisation historique
        cursor.execute("SELECT MIN(DATE(created_at)) FROM orders")
        first_order_date = cursor.fetchone()[0]

        if first_order_date:
            cursor.execute("SELECT period FROM analytics WHERE period_type = ?", (period_type,))
            existing_dates = {row[0] for row in cursor.fetchall()}

            current_date = datetime.strptime(first_order_date, '%Y-%m-%d')
            end_date = datetime.now()
            while current_date <= end_date:
                current_date_str = current_date.strftime('%Y-%m-%d')
                if current_date_str not in existing_dates:
                    cursor.execute("SELECT SUM(total_price) FROM orders WHERE DATE(created_at) = ?", (current_date_str,))
                    total_revenue = cursor.fetchone()[0] or 0.0

                    cursor.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = ?", (current_date_str,))
                    total_orders = cursor.fetchone()[0] or 0

                    cursor.execute("""
                        SELECT COUNT(DISTINCT customer_id)
                        FROM orders
                        WHERE DATE(created_at) = ? AND customer_id IS NOT NULL
                    """, (current_date_str,))
                    customer_count = cursor.fetchone()[0] or 0

                    average_order_value = total_revenue / total_orders if total_orders > 0 else 0.0
                    cltv = total_revenue / customer_count if customer_count > 0 else 0.0

                    cursor.execute("""
                        INSERT INTO analytics (
                            period, period_type,
                            total_revenue, total_orders,
                            average_order_value, cltv, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        current_date_str, period_type,
                        total_revenue, total_orders,
                        average_order_value, cltv,
                        updated_at
                    ))
                current_date += timedelta(days=1)

        logger.info(f"[{shop}] Calcul et synchronisation analytics terminés")

    except Exception as e:
        logger.error(f"[{shop}] Erreur lors du calcul des métriques : {e}")
    finally:
        conn.commit()
        conn.close()
    