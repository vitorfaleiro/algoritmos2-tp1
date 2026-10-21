from math import isfinite
from time import perf_counter

from src.geohash import codificarGeohash, cobrirRaio
from src.geometria import distanciaKm
from src.trie import TrieCompacta


class MotorBusca:
    def __init__(self, entregadores):
        self.entregadores = {item["id"]: item for item in entregadores}
        if len(self.entregadores) != len(entregadores):
            raise ValueError("IDs de entregadores devem ser únicos.")
        self.trie = TrieCompacta()
        for item in entregadores:
            chave = codificarGeohash(item["latitude"], item["longitude"])
            self.trie.inserir(chave, item["id"])

    def consultar(self, latitude, longitude, raioKm, velocidadeKmh=25):
        if not isfinite(velocidadeKmh) or velocidadeKmh <= 0:
            raise ValueError("A velocidade deve ser positiva e finita.")
        inicio = perf_counter()
        prefixos = cobrirRaio(latitude, longitude, raioKm)
        candidatos = set()
        for prefixo in prefixos:
            candidatos.update(self.trie.buscarPrefixo(prefixo))
        filtrados = []
        for entregadorId in candidatos:
            item = self.entregadores[entregadorId]
            distancia = distanciaKm(latitude, longitude, item["latitude"], item["longitude"])
            if distancia <= raioKm + 1e-9:
                filtrados.append({**item, "distanciaKm": distancia,
                                  "tempoMin": distancia / velocidadeKmh * 60})
        fimFiltro = perf_counter()
        filtrados.sort(key=lambda item: (item["distanciaKm"], item["id"]))
        return {"entregadores": filtrados, "candidatos": len(candidatos),
                "prefixos": prefixos, "filtroMs": (fimFiltro - inicio) * 1000,
                "consultaMs": (perf_counter() - inicio) * 1000}
