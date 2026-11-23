"""Gerar a base vetorial local a partir do FAQ em texto UTF-8."""

import os

import chromadb

diretorio_base = os.path.dirname(os.path.abspath(__file__))
caminho_faq = os.path.join(diretorio_base, "dados", "faq_bevans.txt")

with open(caminho_faq, "r", encoding="utf-8-sig") as arquivo:
    texto = arquivo.read().strip()

if not texto:
    raise ValueError("O FAQ esta vazio; verifique dados/faq_bevans.txt.")

tamanho_chunk = 450
overlap = 80
chunks = []
inicio = 0

while inicio < len(texto):
    chunks.append(texto[inicio : inicio + tamanho_chunk])
    inicio += tamanho_chunk - overlap

caminho_banco = os.path.join(diretorio_base, "dados", "banco_vetorial_faq")
cliente_chroma = chromadb.PersistentClient(path=caminho_banco)

try:
    cliente_chroma.delete_collection(name="faq_colecao")
except ValueError:
    pass

colecao = cliente_chroma.get_or_create_collection(
    name="faq_colecao",
    metadata={"hnsw:space": "cosine"},
)

ids = [f"chunk_{i}" for i in range(len(chunks))]
colecao.upsert(ids=ids, documents=chunks)
print(f"{len(chunks)} chunks do BeVans salvos com sucesso!")

pergunta = "Como o passageiro entra em uma turma fixa?"
resultado = colecao.query(
    query_texts=[pergunta],
    n_results=min(5, len(chunks)),
)
print("\n--- Teste de Busca ---")
print("Pergunta:", pergunta)
print("Trecho mais relevante encontrado:")
print(resultado["documents"][0][0].strip())
