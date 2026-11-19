import os
import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# 1. CARREGA CHAVE OPENAI E BANCO VETORIAL
load_dotenv()
cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
modelo = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

diretorio_base = os.path.dirname(os.path.abspath(__file__))
caminho_banco = os.path.join(diretorio_base, "dados", "banco_vetorial_faq")

cliente_chroma = chromadb.PersistentClient(path=caminho_banco)
colecao = cliente_chroma.get_collection(name="faq_colecao")

# 2. INICIA A API FASTAPI E LIBERA CORS PARA O FRONT-END
app = FastAPI(title="API Suporte BeVans")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

regras = (
    "Você é o assistente virtual de suporte do aplicativo BeVans. "
    "Fale de forma natural, amigável, acolhedora e objetiva, como um atendente humano prestativo. "
    "Use APENAS as informações presentes no 'Contexto do FAQ' fornecido em cada mensagem.\n\n"
    "REGRAS DE PERFIL (MOTORISTA VS. PASSAGEIRO):\n"
    "1. Sempre verifique no histórico da conversa se o usuário já informou ou deixou claro se é Motorista ou Passageiro.\n"
    "2. Se ele JÁ disse o perfil antes, NÃO pergunte novamente — responda diretamente adaptado ao perfil dele.\n"
    "3. Se ele ainda NÃO informou o perfil e a pergunta tiver respostas diferentes para motorista e passageiro "
    "(como 'como faço cadastro?', 'como entro na turma?' ou 'como funciona o código?'), "
    "pergunte de forma simpática se ele é motorista ou passageiro antes de explicar.\n"
    "4. Se a pergunta já deixar claro o perfil (ex: 'como crio uma turma?' ou 'como marco que vou na van?') "
    "ou for geral do app, responda direto sem precisar perguntar o perfil.\n\n"
    "Se a resposta não estiver no FAQ, diga educadamente que não possui essa informação e oriente a acessar "
    "o suporte na aba Perfil do aplicativo."
)

class MensagemChat(BaseModel):
    pergunta: str
    historico: list[dict] = []

@app.post("/chat")
def conversar(dados: MensagemChat):
    consulta_busca = dados.pergunta
    if len(dados.historico) >= 2:
        ultima_fala_usuario = dados.historico[-2].get("content", "")
        consulta_busca = f"{ultima_fala_usuario} {dados.pergunta}"

    resultado = colecao.query(
        query_texts=[consulta_busca],
        n_results=3
    )
    contexto = "\n---\n".join(resultado["documents"][0])

    mensagens_para_api = [{"role": "system", "content": regras}] + dados.historico + [
        {
            "role": "user",
            "content": f"Contexto do FAQ do BeVans:\n{contexto}\n\nMensagem do usuário: {dados.pergunta}"
        }
    ]

    resposta = cliente.chat.completions.create(
        model=modelo,
        messages=mensagens_para_api,
        temperature=0.3
    )

    return {"resposta": resposta.choices[0].message.content}
    