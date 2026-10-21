import json
from math import floor

from src.geometria import paraPlano, paraCoordenadas, projetarNoSegmento


class MalhaViaria:
    def __init__(self, linhas):
        self.linhas = linhas
        self.segmentos = []
        self.grade = {}
        self.tamanhoCelula = 0.25  # km
        for linha in linhas:
            for inicio, fim in zip(linha, linha[1:]):
                a, b = paraPlano(*inicio), paraPlano(*fim)
                indice = len(self.segmentos)
                self.segmentos.append((a, b))
                xInicial, yInicial = self.celula(min(a[0], b[0]), min(a[1], b[1]))
                xFinal, yFinal = self.celula(max(a[0], b[0]), max(a[1], b[1]))
                for x in range(xInicial, xFinal + 1):
                    for y in range(yInicial, yFinal + 1):
                        self.grade.setdefault((x, y), []).append(indice)
        if not self.segmentos:
            raise ValueError("A malha não contém segmentos transitáveis.")

    def celula(self, x, y):
        return floor(x / self.tamanhoCelula), floor(y / self.tamanhoCelula)

    def projetar(self, latitude, longitude):
        ponto = paraPlano(latitude, longitude)
        coluna, linha = self.celula(*ponto)
        melhorPonto, melhorDistancia = None, float("inf")
        visitados = set()
        # Para quando as células externas não puderem melhorar a projeção.
        for camada in range(80):
            for x in range(coluna - camada, coluna + camada + 1):
                for y in range(linha - camada, linha + camada + 1):
                    if camada and max(abs(x - coluna), abs(y - linha)) != camada:
                        continue
                    for indice in self.grade.get((x, y), []):
                        if indice in visitados:
                            continue
                        visitados.add(indice)
                        projecao, distancia = projetarNoSegmento(ponto, *self.segmentos[indice])
                        if distancia < melhorDistancia:
                            melhorPonto, melhorDistancia = projecao, distancia
            tamanho = self.tamanhoCelula
            distanciaBorda = min(ponto[0] - (coluna - camada) * tamanho,
                                 (coluna + camada + 1) * tamanho - ponto[0],
                                 ponto[1] - (linha - camada) * tamanho,
                                 (linha + camada + 1) * tamanho - ponto[1])
            if melhorDistancia <= distanciaBorda:
                return (*paraCoordenadas(*melhorPonto), melhorDistancia)
        # mantém a correção exata no plano em pontos muito distantes da malha
        for segmento in self.segmentos:
            projecao, distancia = projetarNoSegmento(ponto, *segmento)
            if distancia < melhorDistancia:
                melhorPonto, melhorDistancia = projecao, distancia
        return (*paraCoordenadas(*melhorPonto), melhorDistancia)

    @classmethod
    def carregar(cls, caminho):
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        return cls(dados["linhas"])
