from flask import Blueprint, request, jsonify
from utils.shopify_utils import execute_graphql_query
from utils.database import save_products_to_db, save_orders_to_db, save_customers_to_db, save_order_items_to_db
from utils.metrics import calculate_product_metrics
import logging

# === CONFIGURATION DU LOGGER ===
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

graphql_bp = Blueprint('graphql', __name__)

# Route pour synchroniser les produits depuis Shopify
@graphql_bp.route('/sync-products', methods=['POST'])
def sync_products():
    shop = request.json.get("shop")
    if not shop:
        return jsonify({"error": "Domaine Shopify non spécifié."}), 400

    # Requête GraphQL pour récupérer les produits
    query = """
    query {
      products(first: 250) {
        edges {
          node {
            id
            title
            variants(first: 250) {
              edges {
                node {
                  price
                  inventoryQuantity
                  inventoryItem {
                    unitCost {
                      amount
                    }
                  }
                }
              }
            }
            status
            createdAt
            updatedAt
          }
        }
      }
    }
    """
    try:
      # Exécuter la requête GraphQL
      data = execute_graphql_query(shop, query)

      if "error" in data:
        logger.error(f"Erreur lors de la requête GraphQL pour les produits {shop} : {data['error']}")
        return jsonify(data), 400

      # Stocker les produits dans la base dédiée à la boutique
      save_products_to_db(shop, data["data"]["products"]["edges"])
      logger
      return jsonify({"message": f"Produits synchronisés avec succès pour {shop}."})
    except Exception as e:
      logger.error(f"Erreur lors de la synchronisation des produits pour {shop} : {str(e)}")
      return jsonify({"error": "Erreur lors de la synchronisation des produits."}), 500

# Route pour synchroniser les commandes depuis Shopify
@graphql_bp.route('/sync-orders', methods=['POST'])
def sync_orders():
    shop = request.json.get("shop")
    if not shop:
        return jsonify({"error": "Domaine Shopify non spécifié."}), 400

    logger.info(f"Synchronisation des commandes pour {shop}...")
    
    # Requête GraphQL pour récupérer les commandes
    query = """
    query {
      orders(first: 250) {
        edges {
          node {
            id
            name
            displayFulfillmentStatus
            totalPriceSet {
              shopMoney {
                amount
              }
            }
            totalDiscountsSet{
              shopMoney{
                amount
              }
            }
            totalTaxSet{
              shopMoney{
                amount
              }
            }
            totalShippingPriceSet{
              shopMoney{
                amount
              }
            }
            createdAt
            customer {
              id
            }
            lineItems(first: 250) {
              edges {
                node {
                  id
                  quantity
                  originalUnitPriceSet {
                    shopMoney {
                      amount
                    }
                  }
                  product {
                    id
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    try:
      # Exécuter la requête
      data = execute_graphql_query(shop, query)

      if "error" in data:
        logger.error(f"Erreur lors de la requête GraphQL pour les commandes {shop} : {data['error']}")
        return jsonify(data), 400

      orders = data["data"]["orders"]["edges"]

      # Stocker les commandes et leurs articles dans SQLite
      save_orders_to_db(shop, orders)

      # Extraire et stocker les articles de commande
      order_items = []
      for order_edge in orders:
          order = order_edge["node"]
          for item_edge in order["lineItems"]["edges"]:
              item = item_edge["node"]
              order_items.append({
                  "order_id": order["id"].split("/")[-1],
                  "product_id": item["product"]["id"].split("/")[-1],
                  "quantity": item["quantity"],
                  "price": float(item["originalUnitPriceSet"]["shopMoney"]["amount"]) * int(item["quantity"]),
              })

      save_order_items_to_db(shop, order_items)
      logger.info(f"Commandes synchronisées avec succès pour {shop}.")
      return jsonify({"message": f"Commandes synchronisées avec succès pour {shop}."})
    except Exception as e: 
      logger.error(f"Erreur lors de la synchronisation des commandes pour {shop} : {str(e)}")
      return jsonify({"message": f"Commandes synchronisées avec succès pour {shop}."})

@graphql_bp.route('/sync-customers', methods=['POST'])
def sync_customers():
    shop = request.json.get("shop")
    if not shop:
      logger.error(f"Erreur lors de la synchronisation des clients pour {shop} : Domaine Shopify non spécifié.")
      return jsonify({"error": "Domaine Shopify non spécifié."}), 400

    query = """
    query {
      customers(first: 250) {
        edges {
          node {
            id
            displayName
            email
            lifetimeDuration
            addresses(first: 1) {
              country
            }
            numberOfOrders
            amountSpent {
              amount
            }
            emailMarketingConsent{
              marketingState
            }
            orders(first: 1, sortKey: PROCESSED_AT, reverse: true) {
              edges {
                node {
                  processedAt
                }
              }
            }
            createdAt
          }
        }
      }
    }
    """
    try:
      data = execute_graphql_query(shop, query)

      if "error" in data:
          return jsonify(data), 400

      save_customers_to_db(shop, data["data"]["customers"]["edges"])
      logger.info(f"Clients synchronisés avec succès pour {shop}.")
      return jsonify({"message": f"Clients synchronisés avec succès pour {shop}."})
    except Exception as e:
      logger.error(f"Erreur lors de la synchronisation des clients pour {shop} : {str(e)}")
      return jsonify({"message": f"Clients synchronisés avec succès pour {shop}."})

@graphql_bp.route('/sync-all', methods=['POST'])
def sync_all():
    shop = request.json.get("shop")
    if not shop:
      logger.error(f"Erreur lors de la synchronisation complète pour {shop} : Domaine Shopify non spécifié.")
      return jsonify({"error": "Domaine Shopify non spécifié."}), 400
    
    logger.info(f"Debut synchronisation complète pour {shop}...")
    
    try:
      # Synchroniser les produits
      products_response = sync_products()
      if products_response.status_code != 200:
        logger.error(f"Erreur lors de la synchronisation des produits pour {shop} :")
        return products_response

      # Synchroniser les commandes
      orders_response = sync_orders()
      if orders_response.status_code != 200:
        logger.error(f"Erreur lors de la synchronisation des commandes pour {shop} :")
        return orders_response

      # Synchroniser les clients
      customers_response = sync_customers()
      if customers_response.status_code != 200:
        logger.error(f"Erreur lors de la synchronisation des clients pour {shop} :")
        return customers_response
        
      calculate_product_metrics(shop)
      logger.info(f"Toutes les données ont été synchronisées pour {shop}.")
      return jsonify({"message": f"Toutes les données ont été synchronisées pour {shop}."})
    except Exception as e:
      logger.error(f"Erreur lors de la synchronisation complète pour {shop} : {str(e)}")
      return jsonify({"error": f"Erreur lors de la synchronisation complète pour {shop}."}), 500