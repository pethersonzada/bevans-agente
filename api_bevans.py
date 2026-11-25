import os
import secrets
from collections import deque
from threading import Lock
from time import monotonic
from typing import Annotated, Literal

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, StringConstraints, field_validator

from agente import responder
from suporte import sensivel

load_dotenv()
app = FastAPI(title="Suporte BeVans", version="1.1")
origens = [o.strip() for o in os.getenv("BEVANS_CORS_ORIGINS", "").split(",") if o.strip() and o.strip() != "*"]
if origens:
    app.add_middleware(CORSMiddleware, allow_origins=origens, allow_methods=["POST"],
                       allow_headers=["Authorization", "Content-Type"])

Texto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1200)]


class Mensagem(BaseModel):
    role: Literal["user", "assistant"]
    content: Texto


class Consulta(BaseModel):
    pergunta: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    historico: list[Mensagem] = Field(default_factory=list, max_length=12)
    perfil: Literal["motorista", "passageiro", ""] = ""

    @field_validator("perfil", mode="before")
    @classmethod
    def normalizar_perfil(cls, valor):
        return valor.lower() if isinstance(valor, str) else valor


@app.exception_handler(RequestValidationError)
async def entrada_invalida(request, exc):
    return JSONResponse({"detail": "Confira a pergunta, o perfil e o histórico."}, status_code=422)


janela = deque()
trava = Lock()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def conversar(dados: Consulta, response: Response, authorization: str = Header(default="")):
    token = os.getenv("BEVANS_API_TOKEN", "")
    if token and not secrets.compare_digest(authorization.encode(), ("Bearer " + token).encode()):
        raise HTTPException(401, "Credencial de serviço inválida.")
    agora = monotonic()
    with trava:
        while janela and janela[0] <= agora - 60:
            janela.popleft()
        if len(janela) >= 60:
            raise HTTPException(429, "Limite temporário de consultas.", headers={"Retry-After": "60"})
        janela.append(agora)
    if sensivel(dados.pergunta) or any(sensivel(m.content) for m in dados.historico):
        raise HTTPException(422, "Remova os dados pessoais ou credenciais da conversa.")
    try:
        resultado = responder(dados.pergunta, [m.model_dump() for m in dados.historico],
                              dados.perfil, os.getenv("OPENAI_API_KEY", ""))
    except (ValueError, OSError):
        raise HTTPException(503, "Base de suporte indisponível.") from None
    response.headers["Cache-Control"] = "no-store"
    return {"resposta": resultado.resposta}
