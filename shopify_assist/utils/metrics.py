import sqlite3
from utils.database import get_database_path
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict

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

    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_order_items_unique ON order_items(order_id, product_id);")

    conn.commit()
    conn.close()


# Fonction principale de calcul des métriques
def calculate_product_metrics(shop):
    db_path = get_database_path(shop)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Date du jour au format YYYY-MM-DD
    today = datetime.now().strftime('%Y-%m-%d')
    period_type = "daily"
    updated_at = datetime.now().isoformat()

    add_product_metrics_columns(shop)

    # Recalcul produit : uniquement avec les commandes du jour
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

    for product_id, qty, revenue, cost in cursor.fetchall():
        cost = cost or 0.0
        if cost is None or cost == 0:
            margin_total = 0.0
        else:
            margin_total = revenue - (cost * qty)

        cursor.execute("""
            UPDATE products
            SET quantity_sold = ?, revenue = ?, margin = ?
            WHERE id = ?
        """, (qty, revenue, margin_total, product_id))

    # Taux de croissance day
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

    for product_id, days in data.items():
        rev_today = days.get(today, 0.0)
        rev_yesterday = days.get(yesterday, 0.0)
        growth = ((rev_today - rev_yesterday) / rev_yesterday * 100) if rev_yesterday else 0.0

        cursor.execute("""
            UPDATE products
            SET growth_rate = ?
            WHERE id = ?
        """, (growth, product_id))

    # Table analytics (granularité daily) avec filtrage sur les données du jour
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

    # ===== DÉBUT DE LA SYNCHRONISATION HISTORIQUE =====
    
    # 1. Récupérer la date de la première commande dans la base
    cursor.execute("SELECT MIN(DATE(created_at)) FROM orders")
    first_order_date = cursor.fetchone()[0]
    
    if first_order_date:  # Si au moins une commande existe
        # 2. Récupérer toutes les dates existantes dans analytics pour éviter les doublons
        cursor.execute("SELECT period FROM analytics WHERE period_type = ?", (period_type,))
        existing_dates = {row[0] for row in cursor.fetchall()}
                
        # 3. Créer une liste de toutes les dates manquantes entre la première commande et aujourd'hui
        start_date = datetime.strptime(first_order_date, '%Y-%m-%d')
        end_date = datetime.now()
        
        dates_to_add = []
        current_date = start_date
        while current_date <= end_date:
            current_date_str = current_date.strftime('%Y-%m-%d')
            
            # N'ajouter que les dates qui n'existent pas déjà
            if current_date_str not in existing_dates:
                dates_to_add.append(current_date_str)
            
            current_date += timedelta(days=1)
        
        # 4. Trier les dates pour s'assurer qu'elles sont insérées dans l'ordre chronologique
        dates_to_add.sort()
        
        for current_date_str in dates_to_add:
            # Calculer les métriques pour cette date spécifique
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
            
            # Calculer les moyennes uniquement s'il y a des données
            average_order_value = total_revenue / total_orders if total_orders > 0 else 0.0
            cltv = total_revenue / customer_count if customer_count > 0 else 0.0
            
            # Insérer la nouvelle entrée
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
            
    # ===== FIN DE LA SYNCHRONISATION HISTORIQUE =====
    
    conn.commit()
    conn.close()