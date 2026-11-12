import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import AIMessage, HumanMessage

load_dotenv()
from graph import ask  # noqa: E402

st.title("Support client multi-agents")
customer = st.sidebar.selectbox("Client connecté (simulé)", ["C1", "C2"])
st.sidebar.caption("C1 possède les commandes 1042–1045 et 1047. C2 possède 1046.")
if st.sidebar.button("Nouvelle conversation"):
    st.session_state.history = []

if "history" not in st.session_state:
    st.session_state.history = []

for m in st.session_state.history:                      # réaffiche la conversation
    st.chat_message("user" if m.type == "human" else "assistant").write(m.content)

msg = st.chat_input("Votre message")
if msg:
    st.chat_message("user").write(msg)
    state = ask(msg, customer, st.session_state.history)
    d = state["decision"]
    st.chat_message("assistant").write(d["answer"])
    st.session_state.history += [HumanMessage(msg), AIMessage(d["answer"])]
    with st.expander("Sous le capot (State final)"):
        st.write("**Chemin :**", " → ".join(state["steps"]))
        st.write("**Statut :**", d["status"], "| **Règle :**", d.get("rule_source"),
                 "| **Raison d'escalade :**", d.get("why"))
        st.json({"order": state["order"], "decision": d})