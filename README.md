# BeVans | Agente de Suporte com RAG

Protótipo de assistente de suporte do **BeVans** que responde a perguntas sobre o produto a partir de um FAQ local. A solução aplica **RAG (Retrieval-Augmented Generation)**: recupera trechos relevantes de uma base vetorial e os envia, junto com a pergunta, a um modelo de linguagem.

**Repositório:** [pethersonzada/bevans-agente](https://github.com/pethersonzada/bevans-agente)  
**Ecossistema:** [Mobile](https://github.com/pethersonzada/bevans-frontend) · [Backend](https://github.com/pethersonzada/bevans-backend) · [WebApp](https://github.com/pethersonzada/bevans-webapp)

## Tecnologias

- **Python**, **OpenAI Python SDK** e modelo de chat configurável (`gpt-4o-mini` por padrão).
- **ChromaDB**, com coleção persistente `faq_colecao`.
- **FastAPI** e **Pydantic** para o endpoint de conversa.
- `python-dotenv` para ler configurações locais.
- `pypdf` no script de indexação; `sentence-transformers` também consta nas dependências.

## Como funciona

```text
Pergunta + histórico do usuário
            |
            v
   Busca semântica no ChromaDB
         (3 trechos)
            |
            v
Contexto de FAQ + instruções + histórico
            |
            v
      OpenAI Chat Completions
            |
            v
         Resposta textual
```

O prompt direciona o atendimento aos perfis **motorista** e **passageiro**, evita repetir perguntas sobre o perfil quando já existe contexto e orienta encaminhar ao suporte do aplicativo quando a informação não estiver presente no FAQ. Essas instruções reduzem respostas fora de escopo, mas **não garantem ausência de alucinações**.

## Arquivos do projeto

```text
api_bevans.py                    # API FastAPI e endpoint POST /chat
chat_rag.py                      # interface de conversa no terminal
criar_banco.py                   # criação/recriação da coleção vetorial
requirements.txt                 # bibliotecas do protótipo
teste_api.py                      # exemplo de chamada direta à OpenAI
dados/
  faq_bevans.txt                 # fonte de conhecimento em texto
  banco_vetorial_faq/            # banco Chroma persistido
.gitignore
```

### Fluxo do endpoint

`POST /chat` recebe um objeto com `pergunta` e, opcionalmente, `historico`. Recupera até três documentos da coleção `faq_colecao`, prepara as mensagens e chama `cliente.chat.completions.create`, com `temperature=0.3`. Retorna um objeto JSON com a propriedade `resposta`.

Exemplo de corpo:

```json
{
  "pergunta": "Como entro em uma turma?",
  "historico": []
}
```

Resposta esperada no contrato:

```json
{
  "resposta": "Texto produzido pelo assistente com base no contexto recuperado."
}
```

## Instalação local

```bash
git clone https://github.com/pethersonzada/bevans-agente.git
cd bevans-agente
python -m venv .venv
```

Ative o ambiente virtual:

```bash
# Linux/macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Depois instale as dependências:

```bash
pip install -r requirements.txt
pip install fastapi uvicorn
```

**Por que a segunda instalação?** O código `api_bevans.py` importa FastAPI, mas `requirements.txt`, na versão consultada, **não declara `fastapi` nem `uvicorn`**. Incluí-los em `requirements.txt` é uma correção recomendada para reproduzibilidade.

Crie `.env` na raiz:

```dotenv
OPENAI_API_KEY=SUA_CHAVE_OPENAI
OPENAI_CHAT_MODEL=gpt-4o-mini
```

Nunca versione `.env` nem exponha a chave em clientes web ou mobile.

## Indexação do FAQ: ajuste necessário

**Existe um problema conhecido na versão consultada:** `criar_banco.py` faz:

```python
caminho_pdf = os.path.join(diretorio_base, "dados", "faq_bevans.txt")
leitor = PdfReader(caminho_pdf)
```

O arquivo fornecido é `.txt`, enquanto `PdfReader` espera um PDF. Isso pode impedir a recriação da base. Corrija o script para abrir o arquivo como texto UTF-8 antes de executar a indexação, por exemplo:

```python
caminho_faq = os.path.join(diretorio_base, "dados", "faq_bevans.txt")
with open(caminho_faq, "r", encoding="utf-8-sig") as arquivo:
    texto = arquivo.read()
```

Preserve depois desse trecho a lógica de divisão em *chunks* e escrita no ChromaDB. O script atual utiliza blocos de **450 caracteres**, sobreposição de **80** e recria a coleção `faq_colecao`; isso elimina o conteúdo anterior dessa coleção. Faça backup se necessário.

Uma vez corrigida a leitura do arquivo, execute:

```bash
python criar_banco.py
```

A API exige que a coleção exista ao importar o módulo, por isso a indexação precisa funcionar antes de iniciar o servidor.

## Executar a API

```bash
uvicorn api_bevans:app --reload --host 127.0.0.1 --port 8000
```

Interface de documentação local do FastAPI: `http://127.0.0.1:8000/docs`.

Teste de requisição:

```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H 'Content-Type: application/json' \
  -d '{"pergunta":"Como entrar em uma turma?","historico":[]}'
```

Para utilizar a interface de linha de comando em vez da API:

```bash
python chat_rag.py
```

A execução requer conectividade com a API OpenAI e pode gerar custos por uso.

## Limitações e melhorias prioritárias

1. **Reprodutibilidade:** corrigir a leitura `.txt` em `criar_banco.py`; adicionar `fastapi` e `uvicorn` às dependências; fixar versões testadas.
2. **Segurança:** `api_bevans.py` utiliza `allow_origins=["*"]` com `allow_credentials=True` e não mostra autenticação ou limite de requisições em `/chat`. Restringir origens, implementar controle de acesso e rate limiting antes de exposição pública.
3. **Histórico:** validar tamanho, estrutura e papéis das mensagens recebidas; não aceitar mensagens `system` arbitrárias de clientes como se fossem instruções confiáveis.
4. **Qualidade do RAG:** criar testes de perguntas do FAQ e de casos sem resposta; revisar pertinência dos trechos recuperados e sinalizar ausência de fontes adequadas.
5. **Governança do FAQ:** o arquivo contém regras atuais e **regras propostas**. Separe conteúdo aprovado de conteúdo planejado para impedir que o agente apresente uma ideia como funcionalidade disponível.
6. **Operação:** adicionar tratamento de falhas da OpenAI/Chroma, métricas sem dados pessoais, políticas de retenção e uma esteira de atualização da base.

> Este repositório é um **protótipo de suporte**. As instruções acima distinguem o comportamento presente no código dos ajustes necessários para uma instalação reprodutível e uma publicação segura.

**Base desta documentação:** commit inicial, `api_bevans.py`, `criar_banco.py`, `chat_rag.py` e `requirements.txt` consultados no GitHub em 21/11/2026.
