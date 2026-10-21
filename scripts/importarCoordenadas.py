# Cruza os bares com a base PBH.
import argparse
import csv
import gzip
import json
import re
import sys
from pathlib import Path

from pyproj import Transformer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.dados import normalizarTexto, raizProjeto

camposChave = ["CNAE_PRINCIPAL", "DESC_LOGRADOURO", "NOME_LOGRADOURO", "NUMERO_IMOVEL",
               "COMPLEMENTO", "NOME_BAIRRO", "NOME", "NOME_FANTASIA"]
fontePbh = "https://dados.pbh.gov.br/pt_BR/dataset/atividade-economica/resource/108d887f-714b-4969-9a37-b959717bac7a"


def chaveEstabelecimento(linha):
    return tuple(" ".join(normalizarTexto(linha[campo]).split()) for campo in camposChave)


def importarCoordenadas(origem, destino, pastaRelatorios=None):
    with gzip.open(raizProjeto / "data/bares.csv.gz", "rt", encoding="utf-8-sig", newline="") as arquivo:
        bares = list(csv.DictReader(arquivo))
    chaves = {chaveEstabelecimento(bar): set() for bar in bares}
    expressaoPonto = re.compile(r"POINT\s*\(\s*([-+\d.eE]+)\s+([-+\d.eE]+)\s*\)")
    totalPbh = 0
    with origem.open(encoding="utf-8-sig", newline="") as arquivo:
        for linha in csv.DictReader(arquivo):
            totalPbh += 1
            chave = chaveEstabelecimento(linha)
            if chave not in chaves:
                continue
            ponto = expressaoPonto.fullmatch(linha["GEOMETRIA"].strip())
            if ponto:
                chaves[chave].add((float(ponto[1]), float(ponto[2])))
    transformador = Transformer.from_crs("EPSG:31983", "EPSG:4326", always_xy=True)
    resultado = []
    pendencias = []
    for bar in bares:
        coordenadas = chaves[chaveEstabelecimento(bar)]
        if len(coordenadas) != 1:
            motivo = "sem correspondência com geometria" if not coordenadas else "mais de uma geometria"
            pendencias.append({"id": bar["_id"], "nome": bar["NOME"], "motivo": motivo})
            continue
        longitude, latitude = transformador.transform(*next(iter(coordenadas)))
        if not (-20.10 <= latitude <= -19.70 and -44.10 <= longitude <= -43.80):
            pendencias.append({"id": bar["_id"], "nome": bar["NOME"], "motivo": "fora da região de BH"})
            continue
        resultado.append({"id": bar["_id"], "latitude": f"{latitude:.8f}", "longitude": f"{longitude:.8f}",
                          "fonte": fontePbh})
    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=["id", "latitude", "longitude", "fonte"])
        escritor.writeheader()
        escritor.writerows(resultado)
    resumo = {"fonte": fontePbh, "crsOrigem": "EPSG:31983", "crsDestino": "EPSG:4326",
              "camposChave": camposChave, "registrosPbh": totalPbh, "bares": len(bares),
              "importados": len(resultado), "pendentes": len(pendencias)}
    if pastaRelatorios is not None:
        pastaRelatorios.mkdir(parents=True, exist_ok=True)
        with (pastaRelatorios / "pendenciasCoordenadas.csv").open("w", encoding="utf-8", newline="") as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=["id", "nome", "motivo"])
            escritor.writeheader()
            escritor.writerows(pendencias)
        (pastaRelatorios / "importacao.json").write_text(json.dumps(resumo, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Importa coordenadas da base da PBH.")
    parser.add_argument("--origem", type=Path, required=True, help="Caminho do CSV da PBH.")
    parser.add_argument("--destino", type=Path, default=raizProjeto / "data/coordenadas.csv")
    parser.add_argument("--relatorios", type=Path, help="Pasta opcional para o resumo e as pendências.")
    argumentos = parser.parse_args()
    importarCoordenadas(argumentos.origem, argumentos.destino, argumentos.relatorios)
