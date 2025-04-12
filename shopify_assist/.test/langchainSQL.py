from langchain_core.prompts import PromptTemplate
from langchain_experimental.sql import SQLDatabaseChain
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
import os

# Charger les variables d'environnement
from dotenv import load_dotenv

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Définir le chemin de la base
db_path = "databases/babaa94_myshopify_com.db"

# Tester la connexion à SQLite
try:
    import sqlite3
    connection = sqlite3.connect(db_path)
    print("Connexion SQLite réussie !")
    connection.close()
except sqlite3.OperationalError as e:
    print(f"Erreur de connexion SQLite : {e}")
    exit()

# Définir le prompt
_DEFAULT_TEMPLATE = """Tu es un assistant Shopify utilisant une base SQLite. Voici le schéma des tables disponibles :

1. Table `products` :
   - `id` : ...
   - `name` : ...
   - `stock` : ...
   - `price` : ...
   - `updated_at` : ...

Génère uniquement des requêtes SQL valides pour SQLite en utilisant ce schéma.

Question : {input}
"""
PROMPT = PromptTemplate(input_variables=["input"], template=_DEFAULT_TEMPLATE)

# Configurer le modèle OpenAI et LangChain
llm = ChatOpenAI(temperature=0.3, openai_api_key=OPENAI_API_KEY)
db = SQLDatabase.from_uri(f"sqlite:///{db_path}")
db_chain = SQLDatabaseChain.from_llm(llm=llm, db=db, prompt=PROMPT, verbose=True)

# Fonction principale
def chatbot_query(query):
    try:
        response = db_chain.invoke(query)
        return response
    except Exception as e:
        return f"Erreur rencontrée : {e}"

if __name__ == "__main__":
    print("Bienvenue dans le chatbot Shopify !")
    print("Posez une question ou tapez 'exit' pour quitter.")
    while True:
        user_query = input("\nVotre question : ")
        if user_query.lower() == "exit":
            print("Merci et à bientôt !")
            break
        print(chatbot_query(user_query))