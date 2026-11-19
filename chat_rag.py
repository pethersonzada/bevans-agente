import os
import chromadb
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
cliente = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
modelo = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

diretorio_base = os.path.dirname(os.path.abspath(__file__))
caminho_banco = os.path.join(diretorio_base, "dados", "banco_vetorial_faq")

cliente_chroma = chromadb.PersistentClient(path=caminho_banco)
colecao = cliente_chroma.get_collection(name="faq_colecao")


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

historico = [{"role": "system", "content": regras}]
print("=" * 60)
print("Suporte BeVans iniciado! Digite sua dúvida ou 'sair'.")
print("=" * 60)


while True:
    pergunta = input("\nVocê: ").strip()

    if pergunta.lower() in ("sair", "exit"):
        print("Até logo! Qualquer dúvida sobre o BeVans, estou por aqui.")
        break

    if not pergunta:
        continue

    consulta_busca = pergunta
    if len(historico) > 1:
        ultima_pergunta_usuario = historico[-2]["content"]
        consulta_busca = f"{ultima_pergunta_usuario} {pergunta}"

    resultado = colecao.query(
        query_texts=[consulta_busca],
        n_results=3
    )
    contexto = "\n---\n".join(resultado["documents"][0])


    mensagens_para_api = historico + [
        {
            "role": "user",
            "content": f"Contexto do FAQ do BeVans:\n{contexto}\n\nMensagem do usuário: {pergunta}"
        }
    ]

    resposta = cliente.chat.completions.create(
        model=modelo,
        messages=mensagens_para_api,
        temperature=0.3
    )

    texto_resposta = resposta.choices[0].message.content

    historico.append({"role": "user", "content": pergunta})
    historico.append({"role": "assistant", "content": texto_resposta})

    print(f"\nAssistente BeVans: {texto_resposta}")