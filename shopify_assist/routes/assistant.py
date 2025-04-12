from flask import Blueprint, request, jsonify
import os 
from shopify_assistant import SQLAssistant

assistant_bp = Blueprint('assistant', __name__)

# Mini-mémoire in-memory : { shop_name: [ { role: "user"/"assistant", content: "..." }, ... ] }
# On en garde seulement quelques messages pour faire un chatbot "semi-stateful".
CONVERSATIONS_STATE = {}

@assistant_bp.route('/conversation', methods=['POST'])
def conversation():
    """
    Semi-stateful: on conserve juste quelques messages du contexte, 
    sans stocker un long historique.
    
    On exploite la classe SQLAssistant pour répondre à chaque question.
    Chaque nouvel appel => on traite la question isolément du point de vue SQLAssistant,
    MAIS on garde côté Flask les 2-3 derniers échanges pour un usage plus "chat".
    
    JSON attendu:
    {
      "shop": "nom-de-boutique",
      "message": "Question utilisateur"
    }
    
    Réponse JSON:
    {
      "assistant_reply": "...",
      "sql": {
          "main_query": "...",
          "context_queries": [...]
        }
    }
    """
    data = request.json
    if not data:
        return jsonify({"error": "Aucune donnée reçue"}), 400

    shop = data.get("shop")
    user_message = data.get("message")
    if not shop or not user_message:
        return jsonify({"error": "Champs 'shop' et 'message' requis"}), 400

    # 1) Récupérer ou initialiser l'historique pour ce shop
    if shop not in CONVERSATIONS_STATE:
        CONVERSATIONS_STATE[shop] = []
    conversation = CONVERSATIONS_STATE[shop]

    # 2) On ajoute le message user à l'historique
    conversation.append({"role": "user", "content": user_message})

    # Limiter à 6 messages max (3 échanges user/assistant)
    if len(conversation) > 6:
        conversation = conversation[-6:]  # On garde les 6 plus récents
    CONVERSATIONS_STATE[shop] = conversation

    # 3) Appel de la classe SQLAssistant pour traiter la question
    # (Cet appel est stateless côté GPT-SQL : il ne tient compte que de la question, pas des tours précédents.)
    try:
        sql_assistant = SQLAssistant(shop)
        result = sql_assistant.process_question(conversation)
    except Exception as e:
        # Si quelque chose se passe mal (connexion DB, etc.)
        assistant_reply = f"Erreur: {str(e)}"
        conversation.append({"role": "assistant", "content": assistant_reply})
        if len(conversation) > 6:
            conversation = conversation[-6:]
        CONVERSATIONS_STATE[shop] = conversation
        return jsonify({"assistant_reply": assistant_reply}), 500

    # 4) Construire la réponse assistant en texte (pour le chat)
    if 'error' in result:
        # Si c'est une erreur détectée dans process_question
        assistant_reply = f"Erreur: {result['error']}"
    else:
        # Soit type='conversational', soit type='data_analysis'
        assistant_reply = result.get('response', "Aucune réponse détectée")

    # On ajoute la réponse assistant à l'historique
    conversation.append({"role": "assistant", "content": assistant_reply})
    if len(conversation) > 6:
        conversation = conversation[-6:]
    CONVERSATIONS_STATE[shop] = conversation

    # 5) Préparer le JSON à renvoyer
    # On peut également renvoyer les queries SQL si on veut les afficher côté front
    response_data = {
        "assistant_reply": assistant_reply
    }
    if result.get("type") == "data_analysis":
        response_data["data"] = result.get("analysis", None)
        response_data["sql"] = {
            "main_query": result.get("main_query"),
            "context_queries": result.get("context_queries")
        }
    elif result.get("type") == "conversational":
        response_data["data"] = None
        response_data["sql"] = None

    return jsonify(response_data)