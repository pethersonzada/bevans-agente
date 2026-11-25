"""Recuperação local sobre respostas revisadas. Nenhum histórico global."""
import json
import math
import re
import unicodedata
from dataclasses import dataclass
from difflib import get_close_matches
from functools import lru_cache
from pathlib import Path

FAQ = Path(__file__).with_name("dados") / "suporte.json"
COMUNS = set("a ao aos as o os de da das do dos e em no na nos nas um uma meu minha me eu como qual quais que quem onde quanto pra para a gente tem pode posso quero esta ta fazer no app bevans van voce sou motorista passageiro".split())
SINONIMOS = dict(entro="entrar", entrar="entrar", cadastrar="cadastro", cadastrar_me="cadastro", crio="criar", marco="marcar", aprovo="aprovar", aceitar="aprovar", aluno="aluno", senha="senha", senah="senha", flia="fila", inicio="iniciar", acesso="acessar", volto="voltar", confirmo="confirmar", recupero="recuperar")
MENSAGENS = {
    "desconhecido": "O FAQ não confirma essa informação. Para valores, horários ou detalhes de uma viagem específica, consulte o responsável pela viagem.",
    "privado": "O assistente não consulta nem fornece dados pessoais de outras pessoas. Para falar com o responsável, use os canais da sua viagem.",
    "seguranca": "Posso orientar sobre o uso do BeVans. Mantenha credenciais e dados pessoais fora do chat.",
    "acao": "O chat só orienta. A ação precisa ser feita por você no aplicativo ou pelo responsável pela viagem.",
    "esclarecer": "Você está falando do cadastro de motorista, do cadastro de passageiro ou do convite para entrar em uma turma?",
}


def normalizar(texto):
    limpo = unicodedata.normalize("NFKD", texto.casefold().replace("e-mail", "email"))
    return " ".join(re.findall("[a-z0-9]+", "".join(c for c in limpo if not unicodedata.combining(c))))


def termos(texto):
    return {SINONIMOS.get(p, p) for p in normalizar(texto).split() if p not in COMUNS}


@dataclass(frozen=True)
class Resultado:
    id: str
    resposta: str
    fonte: str = ""


@lru_cache(maxsize=1)
def carregar(conteudo):
    docs = json.loads(conteudo)
    if not docs or len({d["id"] for d in docs}) != len(docs):
        raise ValueError("Base de suporte vazia ou com IDs repetidos.")
    indice = [(d, [termos(t) for t in d["consultas"]]) for d in docs]
    vocab = set.union(*(t for _, listas in indice for t in listas))
    pesos = {p: 1 + math.log((1 + len(docs)) / (1 + sum(any(p in t for t in listas) for _, listas in indice))) for p in vocab}
    return indice, pesos


def classificar(consulta, perfil, simples=False):
    indice, pesos = carregar(FAQ.read_bytes())
    palavras = termos(consulta)
    if not palavras:
        return []
    if not simples:
        palavras = {p if p in pesos or len(p) < 5 else next(iter(get_close_matches(p, pesos, n=1, cutoff=.82)), p) for p in palavras}
    ranking = []
    for doc, variantes in indice:
        if perfil and doc["perfil"] not in (perfil, "todos"):
            continue
        melhor = 0
        for variante in variantes:
            comuns = palavras & variante
            if simples:
                nota = len(comuns)
            else:
                peso = sum(pesos[p] for p in comuns)
                total = sum(pesos.get(p, 3) for p in palavras)
                nota = peso / math.sqrt(total * sum(pesos[p] for p in variante)) if variante else 0
            melhor = max(melhor, nota)
        if melhor >= (1 if simples else .53):
            ranking.append((melhor, doc))
    return sorted(ranking, key=lambda par: -par[0])


def perfil_texto(texto):
    match = re.search(r"\b(?:sou (?:um |uma )?|perfil (?:de )?)(motorista|passageir[oa]|estudante|condutor)\b", texto)
    valor = match[1] if match else texto
    if valor in ("motorista", "condutor"):
        return "motorista"
    if valor in ("passageiro", "passageira", "estudante"):
        return "passageiro"
    return ""


def restricao(texto):
    if re.search(r"\b(cpf|telefone|endereco|dados)\b.*\b(colega|motorista|outro|outra|terceiro|aluno)\b", texto):
        return "privado"
    if re.search(r"\b(prompt|instrucoes internas|ignore .*instrucoes|chave (da |de )?api|token secreto)\b", texto):
        return "seguranca"
    if re.search(r"^(?:por favor )?(confirme|cancele|apague|altere|marque|reserve|exclua)\b", texto):
        return "acao"
    if re.search(r"\b(preco|custa|valor|horario|mensalidade|reembolso|retencao|quanto tempo .*armazenad)\b", texto):
        return "desconhecido"
    return ""


def sensivel(texto):
    return re.search(r"\b(?:\d{3}\.?\d{3}\.?\d{3}-?\d{2}|sk-[\w-]{12,}|[\w.+-]+@[\w.-]+\.\w+|eyJ[\w.-]{20,})\b|\bminha senha (?:é|e|:)\s*\S+", texto, re.I)


def analisar(pergunta, historico=(), perfil="", simples=False):
    texto = normalizar(pergunta)
    anteriores = [normalizar(m["content"]) for m in historico[-8:] if m["role"] == "user"]
    declarado = perfil_texto(texto)
    papel = declarado or perfil.lower() or next((p for t in reversed(anteriores) if (p := perfil_texto(t))), "")
    motivo = restricao(texto)
    if sensivel(pergunta):
        motivo = "seguranca"
    if motivo:
        return motivo, [], texto, papel
    if anteriores and (re.fullmatch(r"(sou (um |uma )?)?(motorista|passageir[oa]|estudante)", texto) or
                       re.match(r"^(e (na volta|na ida|nessa|ness[ea] caso|se estiver)|e (essa|aquela)|essa turma|aquela viagem)", texto)):
        complemento = re.sub(r"^e se estiver |^e nessa turma$", "", texto)
        texto = anteriores[-1] + " " + complemento
    if not papel and (termos(texto) <= {"cadastro", "conta", "criar", "faco", "codigo", "funciona"}):
        return "esclarecer", [], texto, papel
    candidatos = classificar(texto, papel, simples)
    return "", candidatos, texto, papel


def orientar(pergunta, historico=(), perfil="", simples=False):
    motivo, candidatos, _, _ = analisar(pergunta, historico, perfil, simples)
    if not motivo and candidatos:
        doc = candidatos[0][1]
        return Resultado(doc["id"], doc["resposta"], doc["fonte"])
    motivo = motivo or "desconhecido"
    return Resultado(motivo, MENSAGENS[motivo])
