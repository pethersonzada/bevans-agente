import os
from dotenv import load_dotenv
from agente import responder
from suporte import sensivel


def main():
    load_dotenv()
    historico = []
    print("Suporte BeVans. Digite sair para encerrar ou limpar para recomeçar.")
    while True:
        pergunta = input("Você: ").strip()
        if pergunta.lower() in ("exit", "sair"):
            break
        if pergunta.lower() == "limpar":
            historico.clear()
            continue
        if not 1 <= len(pergunta) <= 1000:
            print("Escreva uma pergunta de até 1000 caracteres.")
            continue
        resposta = responder(pergunta, historico, chave=os.getenv("OPENAI_API_KEY", ""))
        print(resposta.resposta)
        if not sensivel(pergunta):
            historico.extend([dict(role="user", content=pergunta), dict(role="assistant", content=resposta.resposta)])
            historico = historico[-12:]


if __name__ == "__main__":
    main()
