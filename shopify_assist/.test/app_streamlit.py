import streamlit as st
import requests

API_URL = "http://localhost:4000/api/assistant/conversation"

def main():
    st.title("Assistant Shopify (semi-stateful + SQL)")

    # Historique de conversation
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # On stocke manuellement le contenu de la saisie 
    # (pas de clé pour le text_area)
    if "input_text" not in st.session_state:
        st.session_state["input_text"] = ""

    # 1) Historique (en haut)
    st.write("### Historique de la conversation")
    for role, msg in st.session_state["messages"]:
        if role == "user":
            st.markdown(
                f'''
                <div style="background-color:#778899; padding:10px; border-radius:5px; margin-bottom:5px;">
                    <strong>👤 Vous :</strong> {msg}
                </div>
                ''',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'''
                <div style="background-color:#00008b; padding:10px; border-radius:5px; margin-bottom:5px;">
                    <strong>🤖 Assistant :</strong> {msg}
                </div>
                ''',
                unsafe_allow_html=True
            )

    # 2) Champs en bas de la page
    shop = st.text_input("Nom de la boutique :", "ma-boutique")

    # Pas de 'key=' ici, on utilise 'value=' et on gère nous-même la variable input_text
    user_input = st.text_area(
        "Votre question :",
        value=st.session_state["input_text"], 
        height=100
    )

    if st.button("Envoyer"):
        if not user_input.strip():
            st.warning("Veuillez saisir une question.")
        else:
            # Mémoriser la saisie dans le session_state
            st.session_state["input_text"] = user_input

            # Appel de l'API Flask (ou autre)
            payload = {"shop": shop, "message": user_input}
            try:
                resp = requests.post(API_URL, json=payload)
                if resp.status_code == 200:
                    data = resp.json()
                    assistant_reply = data.get("assistant_reply", "")

                    # Ajouter les messages
                    st.session_state["messages"].append(("user", user_input))
                    st.session_state["messages"].append(("assistant", assistant_reply))

                    # Afficher un éventuel SQL
                    if data.get("sql"):
                        st.write("#### 📊 Détails SQL")
                        st.json(data["sql"])

                    # Effacer le champ
                    st.session_state["input_text"] = ""
                else:
                    st.error(f"Erreur HTTP {resp.status_code}: {resp.text}")

            except Exception as e:
                st.error(f"Exception: {str(e)}")

if __name__ == "__main__":
    main()