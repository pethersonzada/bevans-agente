import os
import chromadb
from pypdf import PdfReader

diretorio_base = os.path.dirname(os.path.abspath(__file__))


caminho_pdf = os.path.join(diretorio_base, "dados", "faq_bevans.txt")

leitor = PdfReader(caminho_pdf)
texto = ""
for pagina in leitor.pages:
    texto += (pagina.extract_text() or "") + "\n"


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
except Exception:
    pass

colecao = cliente_chroma.get_or_create_collection(
    name="faq_colecao",
    metadata={"hnsw:space": "cosine"}
)

ids = [f"chunk_{i}" for i in range(len(chunks))]
colecao.upsert(ids=ids, documents=chunks)
print(f"{len(chunks)} chunks do BeVans salvos com sucesso!")

pergunta = "Como o passageiro entra em uma turma fixa?"
resultado = colecao.query(
    query_texts=[pergunta], n_results=5
)
print("\n--- Teste de Busca ---")
print("Pergunta:", pergunta)
print("Trecho mais relevante encontrado:")
print(resultado["documents"][0][0].strip())