Table: analytics
- id (INTEGER)
- period (TEXT) - date (format YYYY-MM-DD)
- period_type (TEXT) - Type ('daily')
- total_revenue (REAL) - Chiffre d'affaires total ce jour-là
- total_orders (INTEGER)
- average_order_value (REAL)
- cltv (REAL) - Valeur vie client moyenne
- updated_at (TEXT)

Table: customers
- id (INTEGER)
- name (TEXT)
- email (TEXT)
- registration (TEXT) - Ancienneté
- country (TEXT)
- number_orders (INTEGER)
- total_spent (REAL)
- email_marketing (TEXT) - Statut de consentement marketing (subscribed, not_subscribed)
- last_order (TEXT)
- created_at (TEXT)

Table: order_items
- id (INTEGER)
- order_id (INTEGER)
- product_id (INTEGER)
- quantity (INTEGER)
- price (REAL) - Prix total (prix unitaire × quantité)

Table: orders
- id (INTEGER)
- name (TEXT)
- status (TEXT)
- total_price (REAL)
- total_discount (REAL)
- total_tax (REAL)
- total_shipping (REAL)
- created_at (TEXT)
- customer_id (INTEGER)

Table: products
- id (INTEGER)
- name (TEXT)
- stock (INTEGER)
- price (REAL)
- cost (REAL)
- status (TEXT)
- created_at (TEXT)
- updated_at (TEXT)
- revenue (REAL) - Chiffre d'affaires total généré par ce produit
- quantity_sold (INTEGER)
- margin (REAL) - Marge brute totale (revenu - coût × quantités)
- growth_rate (REAL) - Taux de croissance du CA (par jour)