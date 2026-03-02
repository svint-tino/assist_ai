# 🛍️ Assistant IA pour e-commerce Shopify

Assistant intelligent alimenté par IA pour analyser et optimiser les données de votre boutique Shopify avec intégration Google Analytics.

## ✨ Fonctionnalités

- 🤖 **Assistant conversationnel** : Posez des questions en langage naturel sur vos données e-commerce
- 📊 **Analyses automatiques** : Génération de requêtes SQL intelligentes et visualisations dynamiques
- 🔗 **Intégration Shopify** : Synchronisation automatique des produits, commandes, clients via GraphQL
- 📈 **Google Analytics 4** : Métriques GA4 intégrées pour une vue complète
- 🎨 **Visualisations Altair** : Graphiques interactifs générés automatiquement par l'IA
- 💬 **Chat contextuel** : L'assistant maintient le contexte de la conversation pour des analyses approfondies

## 🏗️ Architecture

### Backend (Python/Flask)
- **Flask** avec blueprints pour une architecture modulaire
- **SQLite** pour le stockage local des données Shopify
- **OpenAI GPT-4** pour l'analyse intelligente et la génération de SQL
- **Altair** pour la création de visualisations de données
- **SQLAlchemy** pour l'ORM

### Frontend (React/TypeScript)
- **React 18** + **TypeScript** + **Vite** pour un développement rapide
- **TailwindCSS** pour le styling
- **Supabase** pour l'authentification (prototype)
- Interface conversationnelle moderne et responsive

## 📁 Structure du projet

```
assist_ai/
├── shopify_assist/          # Backend Flask
│   ├── routes/              # Endpoints API (Shopify, Google, Assistant)
│   ├── utils/               # Utilitaires (database, metrics, visualizations)
│   ├── prompts/             # Prompts pour l'IA
│   ├── shopify_assistant.py # Logique principale de l'assistant
│   └── app.py               # Point d'entrée Flask
│
└── frontend/                # Frontend React
    ├── src/
    │   ├── components/      # Composants React
    │   ├── App.tsx          # Composant principal
    │   └── AuthContext.tsx  # Gestion de l'authentification
    └── package.json
```

## 🚀 Installation

### Prérequis
- Python 3.9+
- Node.js 18+
- Compte Shopify avec accès API
- Clé API OpenAI

### Backend

```bash
cd shopify_assist
pip install -r requirements.txt

# Créer un fichier .env avec vos credentials
cp .env.example .env
# Éditez .env avec vos clés API

# Lancer le serveur Flask
python app.py
```

Le serveur démarre sur `http://localhost:4000`

### Frontend

```bash
cd frontend
npm install

# Lancer le serveur de développement
npm run dev
```

Le frontend démarre sur `http://localhost:5173`

## 🔧 Configuration

Créez un fichier `.env` dans le dossier `shopify_assist/` :

```env
# Shopify
SHOPIFY_ID=your_shopify_client_id
SHOPIFY_SECRET=your_shopify_client_secret
REDIRECT_URI=http://localhost:4000/api/shopify/redirect

# Google Analytics
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
GOOGLE_REDIRECT_URI=your_google_redirect_uri

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Flask
SECRET_KEY=your_secret_key_here
```

## 💡 Utilisation

1. **Connectez votre boutique Shopify** via OAuth
2. **Synchronisez vos données** (produits, commandes, clients)
3. **Posez des questions** en langage naturel :
   - "Quels sont mes produits les plus vendus ?"
   - "Quel est le chiffre d'affaires du mois dernier ?"
   - "Montre-moi l'évolution des ventes cette année"
4. **L'assistant génère** automatiquement les requêtes SQL et les visualisations

## 🛠️ Technologies utilisées

**Backend**
- Python 3.9+
- Flask (micro-framework web)
- SQLAlchemy (ORM)
- OpenAI API (GPT-4)
- Altair (visualisations)
- Requests (HTTP)

**Frontend**
- React 18
- TypeScript
- Vite (build tool)
- TailwindCSS
- Supabase (auth)

**APIs & Services**
- Shopify GraphQL Admin API
- Google Analytics 4 API
- OpenAI GPT-4 API

## 📊 Fonctionnalités de l'assistant

L'assistant IA peut :
- ✅ Analyser les performances produits
- ✅ Calculer des métriques (revenu, marge, taux de croissance)
- ✅ Générer des visualisations adaptées
- ✅ Répondre à des questions complexes nécessitant plusieurs requêtes
- ✅ Maintenir le contexte de conversation
- ✅ Créer des rapports analytiques en streaming

## ⚠️ Note importante

Ce projet est un **prototype/démo** créé à des fins d'apprentissage et de démonstration. L'authentification Supabase visible dans le code n'est plus active. Le projet illustre l'intégration d'une IA conversationnelle pour l'analyse de données e-commerce.

## 🤝 Contributions

Ce projet est actuellement en archive publique pour portfolio. N'hésitez pas à le forker pour vos propres expérimentations !

## 📄 License

MIT License

## 👤 Auteur

**svint-tino**
- GitHub: [@svint-tino](https://github.com/svint-tino)

---

⭐ Si ce projet vous intéresse, n'hésitez pas à lui donner une étoile !
