from openai import OpenAI
from sqlalchemy import create_engine, text
import json
from dotenv import load_dotenv
import os
from utils.database import get_database_path

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
        
    def generate_analysis(self, conversation: list[dict], main_data: list = None, context_data: list = None) -> str:
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
        
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages_for_gpt,
            temperature=0.5
        )
        
        return response.choices[0].message.content

    def process_question(self, conversation: list[dict]) -> dict:
        """
        conversation = liste de messages
        Le dernier message 'user' contient la question la plus récente
        """
        last_user_question = conversation[-1]["content"]
        
        try:
            query_response = self.generate_sql_query(last_user_question)
            requires_sql = query_response.get("requires_sql", False)
            
            if requires_sql:
                main_query = query_response["main_query"]
                main_data = self.execute_query(main_query)

                context_data = {}
                for ctx in query_response.get('context_queries', []):
                    ctx_name = ctx['name']
                    ctx_query = ctx['query']
                    
                    context_data[ctx_name] = {
                        "data": self.execute_query(ctx_query),
                        "purpose": ctx['purpose']
                    }
                
                analysis = self.generate_analysis(conversation, main_data, context_data)

                return {
                    'type': 'data_analysis',
                    'main_query': main_query,
                    'context_queries': query_response['context_queries'],
                    'response': analysis
                }
            else:
                analysis = self.generate_analysis(conversation, [], {})

                return {
                    'type': 'conversational',
                    'response': analysis
                }
        except Exception as e:
            return {'error': str(e)}