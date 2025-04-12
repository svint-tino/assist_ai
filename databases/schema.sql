BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            period TEXT,
            period_type TEXT DEFAULT 'daily',
            total_revenue REAL DEFAULT 0.0,
            total_orders INTEGER DEFAULT 0,
            average_order_value REAL DEFAULT 0.0,
            cltv REAL DEFAULT 0.0,
            updated_at TEXT
        );
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
    );
CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY,
        order_id INTEGER,
        product_id INTEGER,
        quantity INTEGER,
        price REAL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    );
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
    );
CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        stock INTEGER CHECK(stock >= 0),
        price REAL,
        cost REAL,
        status TEXT,
        created_at TEXT,
        updated_at TEXT
    , revenue REAL DEFAULT 0.0, quantity_sold INTEGER DEFAULT 0, margin REAL DEFAULT 0.0, growth_rate REAL DEFAULT 0.0);
CREATE INDEX idx_customers_country ON customers(country);
CREATE INDEX idx_customers_created_at ON customers(created_at);
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_order_items_order_product ON order_items(order_id, product_id);
CREATE INDEX idx_order_items_product_id ON order_items(product_id);
CREATE INDEX idx_order_items_product_quantity ON order_items(product_id, quantity);
CREATE UNIQUE INDEX idx_order_items_unique ON order_items(order_id, product_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_customer_date ON orders(customer_id, created_at);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_products_name ON products(name);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_stock ON products(stock);
COMMIT;