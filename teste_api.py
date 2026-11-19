import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

chave_api = os.getenv("OPENAI_API_KEY")
cliente = OpenAI(api_key=chave_api)
modelo = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

pergunta = "O que é inteligência artificial?"

print("=" * 60)
print("CHAMADA 1 — sem instrução de 'system' (comportamento padrão)")
print("=" * 60)

resposta = cliente.chat.completions.create(
    model=modelo,
    messages=[{"role": "user", "content": pergunta}],
)

print(resposta.choices[0].message.content)