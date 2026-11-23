# BeVans | Agente de Suporte com RAG

Protótipo de assistente de suporte do **BeVans** que responde a perguntas sobre o produto a partir de um FAQ local. A solução aplica **RAG (Retrieval-Augmented Generation)**: recupera trechos relevantes de uma base vetorial e os envia, junto com a pergunta, a um modelo de linguagem.

**Repositório:** [pethersonzada/bevans-agente](https://github.com/pethersonzada/bevans-agente)  
**Ecossistema:** [Mobile](https://github.com/pethersonzada/bevans-frontend) · [Backend](https://github.com/pethersonzada/bevans-backend) · [WebApp](https://github.com/pethersonzada/bevans-webapp)

## Publicar uma demonstração com Streamlit

Não é necessário abrir o VS Code. O repositório já inclui `streamlit_app.py` e as dependências de hospedagem.

1. Acesse [Streamlit Community Cloud](https://share.streamlit.io) e entre com a conta do GitHub.
2. Selecione **Repository:** `pethersonzada/bevans-agente`, **Branch:** `main` e **Main file path:** `streamlit_app.py`.
3. Abra **Advanced settings**, selecione **Python 3.12** e preencha **Secrets** com o TOML abaixo:

```toml
OPENAI_API_KEY = "SUA_CHAVE_OPENAI_AQUI"
```

4. Salve, clique em **Deploy** e teste uma pergunta sobre o BeVans. A chave acima é apenas um exemplo; use a verdadeira somente no campo privado de Secrets.

**Como funciona:** o Streamlit lê `dados/faq_bevans.txt`, gera embeddings com `text-embedding-3-small` e mantém o índice ChromaDB no armazenamento temporário da instância. O índice pode ser reconstruído após um reinício. As respostas utilizam `gpt-4o-mini` por padrão. A geração de embeddings e respostas consome créditos da API OpenAI.

**Mostrar no webapp da Vercel:** o Streamlit é hospedado separadamente. Depois do deploy, é possível criar uma rota no Next.js com um `iframe`, apontando para a URL REAL do aplicativo Streamlit acrescida de `?embed=true`. Exemplo:

```jsx
export default function AssistentePage() {
  return (
    <iframe
      title="Assistente BeVans"
      src="https://SEU-APP.streamlit.app/?embed=true"
      style={{ width: "100%", height: "80vh", border: 0 }}
    />
  );
}
```

Troque `SEU-APP` pelo subdomínio real. Uma demonstração pública sem autenticação pode consumir créditos da OpenAI; monitore uso e limites. Não envie senhas, CPFs ou tokens de usuários pelo chat.

## Tecnologias

- **Python**, **OpenAI Python SDK** e modelo de chat configurável (`gpt-4o-mini` por padrão).
- **ChromaDB**, com coleção persistente `faq_colecao`.
- **FastAPI** e **Pydantic** para o endpoint de conversa.
- `python-dotenv` para ler configurações locais.
- `streamlit` para a demonstração web; bibliotecas extras do curso preservadas em `requirements-curso.txt`.

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
streamlit_app.py                 # interface do chat no Streamlit
api_bevans.py                    # API FastAPI e endpoint POST /chat
chat_rag.py                      # interface de conversa no terminal
criar_banco.py                   # criação/recriação da coleção vetorial
requirements.txt                 # dependências do Streamlit e da API
requirements-curso.txt           # bibliotecas adicionais do minicurso
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
```

O `requirements.txt` já contém `streamlit`, `fastapi` e `uvicorn`.

Crie `.env` na raiz:

```dotenv
OPENAI_API_KEY=SUA_CHAVE_OPENAI
OPENAI_CHAT_MODEL=gpt-4o-mini
```

Nunca versione `.env` nem exponha a chave em clientes web ou mobile.

## Indexação do FAQ para a API FastAPI

O script `criar_banco.py` já lê `dados/faq_bevans.txt` como UTF-8, divide o conteúdo em blocos de 450 caracteres com sobreposição de 80 e recria a coleção `faq_colecao` no diretório local `dados/banco_vetorial_faq`. Para executá-lo:

```bash
python criar_banco.py
```

A API FastAPI existente utiliza esse banco. Já o Streamlit utiliza um índice separado criado automaticamente a partir do FAQ para facilitar a hospedagem.

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

1. **Reprodutibilidade:** testar o deploy Cloud e, após validar, fixar versões das dependências.
2. **Segurança:** `api_bevans.py` utiliza `allow_origins=["*"]` com `allow_credentials=True` e não mostra autenticação ou limite de requisições em `/chat`. Restringir origens, implementar controle de acesso e rate limiting antes de exposição pública.
3. **Histórico:** validar tamanho, estrutura e papéis das mensagens recebidas; não aceitar mensagens `system` arbitrárias de clientes como se fossem instruções confiáveis.
4. **Qualidade do RAG:** criar testes de perguntas do FAQ e de casos sem resposta; revisar pertinência dos trechos recuperados e sinalizar ausência de fontes adequadas.
5. **Governança do FAQ:** o arquivo contém regras atuais e **regras propostas**. Separe conteúdo aprovado de conteúdo planejado para impedir que o agente apresente uma ideia como funcionalidade disponível.
6. **Operação:** adicionar tratamento de falhas da OpenAI/Chroma, métricas sem dados pessoais, políticas de retenção e uma esteira de atualização da base.

> Este repositório é um **protótipo de suporte**. As instruções acima distinguem o comportamento presente no código dos ajustes necessários para uma instalação reprodutível e uma publicação segura.

**Atualizado em 23/11/2026:** adicionada a demonstração com Streamlit, corrigida a leitura do FAQ e ajustadas as dependências.
