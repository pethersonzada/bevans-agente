"""Avaliação local de intenção, sem chave e sem tráfego de rede."""
from pathlib import Path
from time import perf_counter
from suporte import orientar


def avaliar(simples=False):
    casos = Path(__file__).with_name("tests").joinpath("casos.tsv").read_text().splitlines()
    erros, tempos = [], []
    for linha in casos:
        esperado, *perfil, conversa = linha.split("\t")
        historico = []
        for pergunta in conversa.split(" > "):
            inicio = perf_counter()
            resultado = orientar(pergunta, historico, next(iter(perfil), ""), simples)
            tempos.append(1000 * (perf_counter() - inicio))
            historico.extend([dict(role="user", content=pergunta), dict(role="assistant", content=resultado.resposta)])
        if resultado.id != esperado:
            erros.append((conversa, esperado, resultado.id))
    return len(casos), erros, sorted(tempos)[int(.95 * len(tempos))]


if __name__ == "__main__":
    for simples in (True, False):
        n, erros, p95 = avaliar(simples)
        print("Interseção simples" if simples else "Ranking ponderado", f"{n-len(erros)}/{n}, p95 {p95:.2f} ms")
        for erro in erros:
            print(*erro, sep=" | ")
