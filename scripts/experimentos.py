import csv
import platform
import statistics
import sys
from pathlib import Path
from time import perf_counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.busca import MotorBusca
from src.dados import carregarBares, carregarRestaurantes, raizProjeto
from src.geometria import distanciaKm
from src.ruas import MalhaViaria
from src.simulacao import gerarEntregadores


def executarExperimentos():
    malha = MalhaViaria.carregar(raizProjeto / "data/ruas.json")
    centros = carregarRestaurantes(carregarBares())
    if not centros:
        raise ValueError("Importe as coordenadas dos bares antes de executar os experimentos.")
    linhas = []
    for quantidade in [100, 1000, 5000]:
        inicio = perf_counter()
        frota = gerarEntregadores(quantidade, centros, malha, semente=42)
        geracaoMs = (perf_counter() - inicio) * 1000
        inicio = perf_counter()
        motor = MotorBusca(frota)
        indiceMs = (perf_counter() - inicio) * 1000
        for restaurante in centros[:3]:
            latitude, longitude = restaurante["latitude"], restaurante["longitude"]
            for raio in [0.5, 2, 5]:
                tempos = []
                temposExaustiva = []
                motor.consultar(latitude, longitude, raio)  # aquecimento
                for _ in range(15):
                    resultado = motor.consultar(latitude, longitude, raio)
                    tempos.append(resultado["consultaMs"])
                    inicio = perf_counter()
                    esperado = [item for item in frota if distanciaKm(latitude, longitude, item["latitude"], item["longitude"]) <= raio + 1e-9]
                    temposExaustiva.append((perf_counter() - inicio) * 1000)
                    assert {item["id"] for item in esperado} == {item["id"] for item in resultado["entregadores"]}
                linhas.append({"n": quantidade, "centro": restaurante["nome"], "raioKm": raio,
                               "candidatos": resultado["candidatos"], "encontrados": len(esperado),
                               "celulas": len(resultado["prefixos"]), "geracaoMs": round(geracaoMs, 3),
                               "indiceMs": round(indiceMs, 3), "consultaMedianaMs": round(statistics.median(tempos), 3),
                               "consultaMinMs": round(min(tempos), 3), "consultaMaxMs": round(max(tempos), 3),
                               "exaustivaMedianaMs": round(statistics.median(temposExaustiva), 3)})
    destino = raizProjeto / "docs/experimentos.csv"
    with destino.open("w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=list(linhas[0]))
        escritor.writeheader()
        escritor.writerows(linhas)
    print(f"Python {platform.python_version()} / {platform.platform()}")
    print(f"{len(linhas)} cenários, 15 repetições cada; todos equivalentes à busca exaustiva.")
    print(destino)


if __name__ == "__main__":
    executarExperimentos()
