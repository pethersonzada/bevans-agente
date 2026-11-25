import os
import streamlit as st
from dotenv import load_dotenv
from agente import responder
from suporte import sensivel

load_dotenv()
st.set_page_config(page_title="Assistente BeVans", layout="centered")
st.title("Assistente BeVans")
st.caption("Tire dúvidas sobre turmas, presença e viagens. Evite enviar dados pessoais.")


def limpar():
    st.session_state.mensagens = []


st.session_state.setdefault("mensagens", [])
with st.sidebar:
    perfil = st.selectbox("Como você usa o BeVans?", ["Não informado", "Motorista", "Passageiro"], on_change=limpar)
    st.button("Nova conversa", on_click=limpar)

for mensagem in st.session_state.mensagens:
    with st.chat_message(mensagem["role"]):
        st.text(mensagem["content"])

sugerida = None
if not st.session_state.mensagens:
    opcoes = ["Como entro na turma?", "Quantas paradas faltam?"]
    if perfil == "Motorista":
        opcoes = ["Como criar uma turma?", "Como organizar uma excursão?"]
    for coluna, opcao in zip(st.columns(2), opcoes):
        if coluna.button(opcao):
            sugerida = opcao

pergunta = st.chat_input("Escreva sua dúvida", max_chars=1000) or sugerida
if pergunta and pergunta.strip():
    if sensivel(pergunta):
        st.warning("Retire os dados pessoais ou a credencial e envie a dúvida novamente.")
    else:
        chave = os.getenv("OPENAI_API_KEY", "")
        if not chave:
            try:
                chave = st.secrets.get("OPENAI_API_KEY", "")
            except FileNotFoundError:
                pass
        with st.spinner("Consultando as orientações do BeVans…"):
            try:
                resultado = responder(pergunta, st.session_state.mensagens,
                                      "" if perfil == "Não informado" else perfil.lower(), chave)
            except (OSError, ValueError):
                st.error("A base de suporte está indisponível. Tente novamente mais tarde.")
            else:
                st.session_state.mensagens = (st.session_state.mensagens + [
                    {"role": "user", "content": pergunta},
                    {"role": "assistant", "content": resultado.resposta},
                ])[-24:]
                st.rerun()
