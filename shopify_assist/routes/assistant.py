from flask import Blueprint, request, jsonify, stream_with_context, Response
import os 
import logging
from shopify_assistant import SQLAssistant
from utils.visual_utils import validate_visual_spec, render_altair_visual


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
    
    version utilise le streaming pour envoyer les réponses progressivement.
    """
    data = request.json
    if not data:
        return jsonify({"error": "Aucune donnée reçue"}), 400

    shop = data.get("shop")
    user_message = data.get("message")
    if not shop or not user_message:
        return jsonify({"error": "Champs 'shop' et 'message' requis"}), 400

    # Récupérer ou initialiser l'historique pour ce shop
    if shop not in CONVERSATIONS_STATE:
        CONVERSATIONS_STATE[shop] = []
    conversation = CONVERSATIONS_STATE[shop]

    # Ajouter le message utilisateur à l'historique
    conversation.append({"role": "user", "content": user_message})
    if len(conversation) > 6:
        conversation = conversation[-6:]
    CONVERSATIONS_STATE[shop] = conversation

    def generate_response():
        try:
            sql_assistant = SQLAssistant(shop)
            for chunk in sql_assistant.full_response(conversation):
                yield chunk
        except Exception as e:
            error_message = f"Erreur: {str(e)}"
            yield error_message
            logger.error(f"[{shop}] Erreur dans le traitement de la question: {str(e)}")

    # Ajouter un en-tête pour indiquer que c'est un flux d'événements
    headers = {"Content-Type": "text/plain", "Cache-Control": "no-cache"}
    return Response(stream_with_context(generate_response()), headers=headers)

@assistant_bp.route('/generate-visual', methods=['POST'])
def generate_visual():
    """
    Génère un graphique Altair à partir d'une spécification JSON reçue.
    
    JSON attendu :
    {
      "visual_spec": { ... }
    }

    Réponse :
    {
      "html_path": "/static/abc123.html"
    }
    """
    data = request.json
    if not data:
        return jsonify({"error": "Aucune donnée reçue"}), 400
    
    # Vérifier la présence de la spécification visuelle
    visual_spec = data.get("visual_spec")
    if not visual_spec:
        return jsonify({"error": "Champ 'visual_spec' requis"}), 400

    # Valider la spec
    if not validate_visual_spec(visual_spec):
        return jsonify({"error": "La spécification fournie est invalide."}), 400

    # Générer le visuel
    output_path = render_altair_visual(visual_spec)

    if not output_path:
        return jsonify({"error": "Échec de la génération de la visualisation."}), 500

    # Retourner l’URL accessible depuis le frontend
    public_url = "/" + output_path.lstrip("./")

    return jsonify({"html_path": public_url})