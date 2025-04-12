import sqlite3
import os

# Obtenir le chemin de la base de données pour une boutique donnée
def get_database_path(shop):
    # Nettoyer le nom du shop pour éviter les problèmes de système de fichiers
    safe_shop = shop.replace(".", "_").replace("-", "_")
    db_path = f"databases/{safe_shop}.db"

    # Assurer que le dossier `databases` existe
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return db_path

def create_tables(shop):
    db_path = get_database_path(shop)
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Table des produits
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        stock INTEGER CHECK(stock >= 0),
        price REAL,
        cost REAL,
        status TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_stock ON products(stock);")

    # Table des commandes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY,
        name TEXT,
        status TEXT,
        total_price REAL,
        total_discount REAL,
        total_tax REAL,
        total_shipping REAL,
        created_at TEXT,
        customer_id INTEGER,
        FOREIGN KEY (customer_id) REFERENCES customers(id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer_date ON orders(customer_id, created_at);")

    # Table des clients
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        registration TEXT,
        country TEXT,
        number_orders INTEGER,
        total_spent REAL,
        email_marketing TEXT,
        last_order TEXT,
        created_at TEXT
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_country ON customers(country);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_created_at ON customers(created_at);")

    # Table des articles de commande
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price REAL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_product ON order_items(order_id, product_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_product_quantity ON order_items(product_id, quantity);")

    connection.commit()
    connection.close()

# Sauvegarder les produits
def save_products_to_db(shop, products):
    create_tables(shop)  # Crée les tables si elles n'existent pas

    db_path = get_database_path(shop)
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    for edge in products:
        product = edge["node"]
        variant = product["variants"]["edges"][0]["node"]
        
        # Sécuriser l'accès au coût unitaire (unitCost peut être None)
        unit_cost = 0.0
        if variant.get("inventoryItem") and variant["inventoryItem"].get("unitCost"):
            unit_cost_data = variant["inventoryItem"]["unitCost"]
            if unit_cost_data and unit_cost_data.get("amount"):
                unit_cost = float(unit_cost_data["amount"])

        cursor.execute("""
        INSERT OR REPLACE INTO products (id, name, stock, price, cost, status, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product["id"].split("/")[-1],  # Extraire l'ID réel
            product["title"],
            variant["inventoryQuantity"],
            float(variant["price"]),
            unit_cost,
            product["status"],
            product["createdAt"][:10],
            product["updatedAt"][:10]
        ))

    connection.commit()
    connection.close()
    
# Sauvegarder les commandes
def save_orders_to_db(shop, orders):
    create_tables(shop)  # Assure que les tables sont créées
    db_path = get_database_path(shop)
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()
    
    for edge in orders:
        order = edge["node"]
        customer_id = order["customer"]["id"].split("/")[-1] if order.get("customer") else None
        
        cursor.execute("""
        INSERT OR REPLACE INTO orders (id, name, status, total_price, total_discount, total_tax, total_shipping, created_at, customer_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            order["id"].split("/")[-1],  # Extraire l'ID réel
            order["name"],
            order["displayFulfillmentStatus"],
            float(order["totalPriceSet"]["shopMoney"]["amount"]),
            float(order["totalDiscountsSet"]["shopMoney"]["amount"]),
            float(order["totalTaxSet"]["shopMoney"]["amount"]),
            float(order["totalShippingPriceSet"]["shopMoney"]["amount"]),
            order["createdAt"][:10],
            customer_id  # Référence au client ou None
        ))

    connection.commit()
    connection.close()

# Sauvegarder les clients
def save_customers_to_db(shop, customers):
    create_tables(shop)
    db_path = get_database_path(shop)
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    for edge in customers:
        customer = edge["node"]
        
        country = None
        if customer.get("addresses"):  # Vérifie si 'addresses' existe et n'est pas vide
            first_address = customer["addresses"][0]  # Prend la première adresse
            country = first_address.get("country")  # Récupère le pays si disponible
        
        # Sécurité pour la date de dernière commande
        last_order_date = None
        orders = customer.get("orders", {}).get("edges", [])
        if orders:
            first_order = orders[0].get("node")
            if first_order and first_order.get("processedAt"):
                last_order_date = first_order["processedAt"][:10]


        
        cursor.execute("""
        INSERT OR REPLACE INTO customers (id, name, email, registration, country, number_orders, total_spent, email_marketing, last_order, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer["id"].split("/")[-1],
            customer["displayName"],
            customer["email"],
            customer["lifetimeDuration"],
            country,
            customer["numberOfOrders"],
            float(customer["amountSpent"]["amount"]),
            customer["emailMarketingConsent"]["marketingState"],
            last_order_date,
            customer["createdAt"][:10]
        ))

    connection.commit()
    connection.close()

# Sauvegarder les articles de commande
def save_order_items_to_db(shop, order_items):
    create_tables(shop)
    db_path = get_database_path(shop)
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    for item in order_items:
        # Vérifier s'il existe déjà une ligne avec le même order_id et product_id
        cursor.execute("""
            SELECT 1 FROM order_items WHERE order_id = ? AND product_id = ?
        """, (item["order_id"], item["product_id"]))
        exists = cursor.fetchone()

        if exists:
            # Si la ligne existe, mettre à jour les valeurs
            cursor.execute("""
                UPDATE order_items 
                SET quantity = ?, price = ?
                WHERE order_id = ? AND product_id = ?
            """, (
                item["quantity"],
                item["price"],
                item["order_id"],
                item["product_id"]
            ))
        else:
            # Si la ligne n'existe pas, l'insérer
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (?, ?, ?, ?)
            """, (
                item["order_id"],
                item["product_id"],
                item["quantity"],
                item["price"]
            ))

    connection.commit()
    connection.close()