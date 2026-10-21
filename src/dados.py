import csv
import gzip
import unicodedata
from pathlib import Path

from src.geometria import validarCoordenadas

raizProjeto = Path(__file__).resolve().parents[1]


def normalizarTexto(texto):
    return "".join(letra for letra in unicodedata.normalize("NFD", texto.casefold())
                   if unicodedata.category(letra) != "Mn")


def carregarBares(caminho=None):
    caminho = caminho or raizProjeto / "data/bares.csv.gz"
    with gzip.open(caminho, "rt", encoding="utf-8-sig", newline="") as arquivo:
        bares = []
        for linha in csv.DictReader(arquivo):
            endereco = " ".join(linha[campo].strip() for campo in
                                ["DESC_LOGRADOURO", "NOME_LOGRADOURO", "NUMERO_IMOVEL"])
            bares.append({"id": linha["_id"], "nome": linha["NOME_FANTASIA"] or linha["NOME"],
                          "endereco": endereco, "bairro": linha["NOME_BAIRRO"]})
    return bares


def carregarRestaurantes(bares, caminho=None):
    caminho = caminho or raizProjeto / "data/coordenadas.csv"
    if not caminho.exists():
        return []
    porId = {bar["id"]: bar for bar in bares}
    restaurantes = []
    encontrados = set()
    with caminho.open(encoding="utf-8-sig", newline="") as arquivo:
        leitor = csv.DictReader(arquivo)
        if not {"id", "latitude", "longitude", "fonte"}.issubset(leitor.fieldnames or []):
            raise ValueError("coordenadas.csv deve conter id,latitude,longitude,fonte.")
        for numero, linha in enumerate(leitor, 2):
            barId = linha["id"]
            if barId not in porId or barId in encontrados:
                raise ValueError(f"ID inexistente ou repetido na linha {numero}: {barId}")
            latitude, longitude = float(linha["latitude"]), float(linha["longitude"])
            validarCoordenadas(latitude, longitude)
            if not (-20.10 <= latitude <= -19.70 and -44.10 <= longitude <= -43.80):
                raise ValueError(f"Coordenada fora da região de BH na linha {numero}.")
            if not linha["fonte"].strip():
                raise ValueError(f"Informe a fonte da coordenada na linha {numero}.")
            encontrados.add(barId)
            restaurantes.append({**porId[barId], "latitude": latitude,
                                  "longitude": longitude, "fonte": linha["fonte"]})
    return restaurantes
