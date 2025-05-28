from openai import OpenAI
from sqlalchemy import create_engine, text
import json
from dotenv import load_dotenv
import os
from utils.database import get_database_path
from utils.visual_utils import render_altair_visual


load_dotenv()

class SQLAssistant:
    def __init__(self, shop: str):
        db_path = get_database_path(shop)
        self.engine = create_engine(f"sqlite:///{db_path}")
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def generate_sql_query(self, last_user_question: str) -> dict:
        
        # Charger le schéma Markdown statique
        with open("prompts/schema.md", "r", encoding="utf-8") as f:
            schema = f.read()

        # Construire le message "system" pour donner le contexte + instructions
        system_prompt = f"""Tu es un expert SQL et e-commerce. 
        Voici le schéma de la base de données : 
        
        {schema}

        INSTRUCTIONS :
        - Si la question est simple, ne retourne qu'une seule requête dans `main_query`.
        - Si la question est complexe ou stratégique (analyse, diagnostic, prévision...), ajoute des `context_queries` utiles pour enrichir la réponse.
          
          - Réponds sous la forme JSON suivante :
            {{
                "requires_sql": true,
                "visualisation": true or false,
                "main_query": "SELECT ...",
                "context_queries": [
                    {{
                        "name": "nom_explicite",
                        "query": "SELECT ... FROM ...",
                        "purpose": "Brève explication"
                    }}
                ]
            }}
            
          - Sans formatage Markdown, juste du JSON brut, valide.
          
        Si la question est plutôt conversationnelle ou ne nécessite pas de SQL :
          
          - Réponds sous la forme :
            {{ "requires_sql": false, "response": "Ok" }}

        Limite toutes les requêtes à 100 résultats maximum avec `LIMIT 100` pour éviter les surcharges.
        N'utilise QUE les tables et colonnes présentes dans le schéma.
        Priorise les 'name' plutot que les 'id'
        Respecte scrupuleusement le format JSON demandé.
        """

        # Appel GPT
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": last_user_question}
            ],
            temperature=0
        )

        # Parser la réponse en JSON
        content = response.choices[0].message.content
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Erreur de parsing JSON: {str(e)}")
    
    def execute_query(self, query: str) -> list:
        """Exécute la requête SQL et retourne les résultats"""
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            columns = result.keys()
            records = [dict(zip(columns, row)) for row in result]
            return records
        
    def generate_analysis(self, conversation: list[dict], main_data: list = None, context_data: list = None):
        """Génère une analyse basée sur les données principales et contextuelles"""
        
        if main_data is None:
            main_data = []
        if context_data is None:
            context_data = {}
            
        system_prompt = f"""Tu es un expert e-commerce spécialisé Shopify.

        Données à analyser :
        {json.dumps(main_data, indent=2)}
        {json.dumps(context_data, indent=2)}
        
        Analyse les données suivantes :
        - `main_data` : résultats principaux liés à la question
        - `context_data` : compléments utiles à l'analyse

        Ta mission est de fournir une réponse claire, structurée et actionnable :
        - Si la question est simple, reste synthétique
        - Si elle est stratégique, croise les données pour enrichir l'analyse

        Mets en avant :
        - les tendances, anomalies ou signaux faibles
        - des recommandations concrètes (optimisations, alertes, opportunités)
        - des ratios clés (marge, CLTV, AOV, croissance)

        Style attendu :
        - Professionnel, direct, sans superflu
        - Orienté performance et décisions concrètes
        - Phrase d'accroche possible si pertinente, mais reste utile
        """
        
        messages_for_gpt = [
            {"role": "system", "content": system_prompt},
        ] + conversation
        
        try:
            # Appel à l'API OpenAI avec le mode streaming activé
            stream = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages_for_gpt,
                temperature=0.5,
                stream=True
            )

            # Parcourir les morceaux de réponse et les transmettre
            for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content

        except Exception as e:
            # En cas d'erreur, transmettre un message d'erreur
            yield f"Erreur lors de la génération de l'analyse : {str(e)}"

    def generate_visual_spec(self, question: str, main_data: list[dict]) -> dict:
        """Utilise GPT pour générer une spec Altair JSON à partir d'une question et des données associées"""       
        #Choisis le type de graphique adapté : bar, line, scatter, pie…
        
        system_prompt = f"""Tu es un assistant Python expert en visualisation de données avec Altair.

        Ta mission :
        Génère une spécification Altair (compatible Vega-Lite) en JSON pour représenter les données ci-dessous.

        INSTRUCTIONS :
        1.Utilise EXACTEMENT le format Vega-Lite standard :
        {{
            "data": {{
                "values": [ ... toutes les données ... ]
            }},
            "mark": "bar|line|area|point|circle",
            "encoding": {{
                "x": {{ "field": "nom_du_champ", "type": "quantitative|ordinal|nominal|temporal", "title": "Titre axe X" }},
                "y": {{ "field": "nom_du_champ", "type": "quantitative|ordinal|nominal|temporal", "title": "Titre axe Y" }}
            }},
            "title": "Titre du graphique"
        }}
        
        2. CHOIX DU GRAPHIQUE :
        - "bar" : comparaisons, top N, répartitions
        - "line" : évolutions temporelles, tendances
        - "area" : évolutions avec surface, volumes cumulés
        - "point" : corrélations, dispersions
        - "circle" : scatter plots avec tailles variables

        3. SÉLECTION DES CHAMPS :
        - X : souvent la métrique (quantité, montant, pourcentage)
        - Y : souvent la dimension (catégorie, temps)
        - Utilise UNIQUEMENT les champs présents dans les données

        4. FORMAT DE RÉPONSE :
        - JSON pur, sans balises markdown
        - Inclure TOUTES les données dans "data.values"
        - Titre explicite et professionnel 
               
        Question utilisateur :
        {question}

        Données (main_data) :
        {json.dumps(main_data[:10], indent=2)}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt}
                ],
                temperature=0
            )
            
            # Extraire le contenu de la réponse
            content = response.choices[0].message.content

            # Nettoyer les balises Markdown si présentes
            if content.startswith("```json") and content.endswith("```"):
                content = content[7:-3].strip()  # Supprime les balises ```json et ```

            # Parser le JSON
            return json.loads(content)
        except Exception as e:
            return {"error": f"Erreur dans generate_visual_spec : {str(e)}"}
        
    def full_response(self, conversation: list[dict]):
        """
        Gère la logique SQL si nécessaire, génère une visualisation si demandée, 
        puis stream le résultat de generate_analysis()
        """
        last_user_question = conversation[-1]["content"]

        try:
            query_response = self.generate_sql_query(last_user_question)
            requires_sql = query_response.get("requires_sql", False)
            needs_visualization = query_response.get("visualisation", False)

            main_data = []
            context_data = {}
            visual_spec = None

            if requires_sql:
                main_query = query_response["main_query"]
                main_data = self.execute_query(main_query)

                # Récupération des données contextuelles
                for ctx in query_response.get('context_queries', []):
                    ctx_name = ctx['name']
                    ctx_query = ctx['query']
                    context_data[ctx_name] = {
                        "data": self.execute_query(ctx_query),
                        "purpose": ctx['purpose']
                    }

                # Génération de la visualisation si nécessaire
                if needs_visualization and main_data:
                    visual_spec = self.generate_visual_spec(last_user_question, main_data)
                    
                    output_dir = os.path.join(os.path.dirname(__file__), "static")  # ou current_app.static_folder si tu es dans Flask
                    visual_spec_path = render_altair_visual(visual_spec, output_dir)

                    if visual_spec_path:
                        print("Visualisation générée :", visual_spec_path)
                        # Envoi du lien streamé vers le frontend
                        yield f"[VISUAL] /static/{os.path.basename(visual_spec_path)}"
                        
            # Stream de l'analyse (sans la visualisation dans context_data maintenant)
            for chunk in self.generate_analysis(conversation, main_data, context_data):
                yield chunk

        except Exception as e:
            yield f"Erreur : {str(e)}"