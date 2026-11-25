"""Validar o FAQ local e, com chave configurada, preparar o índice semântico."""
import os
from dotenv import load_dotenv
from agente import cliente_openai, indice
from suporte import FAQ, carregar, orientar


def main():
    load_dotenv()
    try:
        dados = FAQ.read_bytes()
        docs, _ = carregar(dados)
        chave = os.getenv("OPENAI_API_KEY")
        if chave:
            print(f"Índice semântico com {indice(dados, cliente_openai(chave)).count()} orientações.")
        print(f"Base local com {len(docs)} orientações.")
        print(orientar("Como entrar na turma?").resposta)
    except (OSError, ValueError):
        raise SystemExit("Confira o caminho e o conteúdo de dados/suporte.json.") from None


if __name__ == "__main__":
    main()
