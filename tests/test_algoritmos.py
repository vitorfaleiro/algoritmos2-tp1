import random
import unittest
from collections import Counter

from src.busca import MotorBusca
from src.dados import normalizarTexto
from src.geohash import codificarGeohash, decodificarLimites
from src.geometria import distanciaKm, paraCoordenadas, paraPlano, projetarNoSegmento
from src.ruas import MalhaViaria
from src.simulacao import gerarEntregadores
from src.trie import TrieCompacta


class TestGeohash(unittest.TestCase):
    def testVetoresConhecidos(self):
        self.assertEqual(codificarGeohash(42.6, -5.6, 5), "ezs42")
        self.assertEqual(codificarGeohash(57.64911, 10.40744, 8), "u4pruydq")
        self.assertEqual(codificarGeohash(0, 0, 1), "s")

    def testLimitesContemPonto(self):
        sorteador = random.Random(7)
        for precisao in range(1, 9):
            for _ in range(100):
                latitude, longitude = sorteador.uniform(-90, 90), sorteador.uniform(-180, 180)
                sul, norte, oeste, leste = decodificarLimites(codificarGeohash(latitude, longitude, precisao))
                self.assertTrue(sul <= latitude <= norte and oeste <= longitude <= leste)

    def testEntradasInvalidas(self):
        for latitude, longitude in [(91, 0), (0, 181), (float("nan"), 0)]:
            with self.assertRaises(ValueError):
                codificarGeohash(latitude, longitude)
        for precisao in [0, 9, 2.5]:
            with self.assertRaises(ValueError):
                codificarGeohash(0, 0, precisao)


class TestTrie(unittest.TestCase):
    def testDivisaoDeArestaDuplicatasEPrefixoInterno(self):
        trie = TrieCompacta()
        chaves = ["abcde", "abcfg", "abcde", "abc", "x", "ab", ""]
        for indice, chave in enumerate(chaves):
            trie.inserir(chave, indice)
        for prefixo in ["", "a", "ab", "abc", "abcd", "abcde", "abcz", "x", "y"]:
            esperado = [indice for indice, chave in enumerate(chaves) if chave.startswith(prefixo)]
            self.assertEqual(sorted(trie.buscarPrefixo(prefixo)), esperado)

    def testCompactacao(self):
        trie = TrieCompacta()
        trie.inserir("abcdef", 1)
        self.assertEqual(trie.raiz.filhos["a"].trecho, "abcdef")
        self.assertEqual(trie.raiz.filhos["a"].filhos, {})

    def testPrefixosAleatorios(self):
        sorteador = random.Random(19)
        chaves = ["".join(sorteador.choices("0123456789bcdefghjkmnpqrstuvwxyz", k=8)) for _ in range(1500)]
        trie = TrieCompacta()
        for indice, chave in enumerate(chaves):
            trie.inserir(chave, indice)
        for _ in range(200):
            prefixo = sorteador.choice(chaves)[:sorteador.randint(0, 8)]
            esperado = [indice for indice, chave in enumerate(chaves) if chave.startswith(prefixo)]
            self.assertEqual(sorted(trie.buscarPrefixo(prefixo)), esperado)


class TestBusca(unittest.TestCase):
    def conferirConsulta(self, pontos, latitude, longitude, raio):
        resultado = MotorBusca(pontos).consultar(latitude, longitude, raio)
        esperado = {ponto["id"] for ponto in pontos if distanciaKm(latitude, longitude, ponto["latitude"], ponto["longitude"]) <= raio + 1e-9}
        self.assertEqual({ponto["id"] for ponto in resultado["entregadores"]}, esperado)
        distancias = [item["distanciaKm"] for item in resultado["entregadores"]]
        self.assertEqual(distancias, sorted(distancias))

    def testBuscaExaustivaComoOraculo(self):
        sorteador = random.Random(42)
        pontos = [{"id": indice, "latitude": sorteador.uniform(-20.05, -19.75),
                   "longitude": sorteador.uniform(-44.05, -43.85)} for indice in range(2000)]
        for _ in range(30):
            self.conferirConsulta(pontos, sorteador.uniform(-20, -19.8), sorteador.uniform(-44, -43.9),
                                  sorteador.choice([0, 0.01, 0.1, 0.5, 2, 10, 40]))

    def testBordasDaGrade(self):
        sul, norte, oeste, leste = decodificarLimites(codificarGeohash(-19.92, -43.94, 6))
        pontos = [{"id": indice, "latitude": norte + dy, "longitude": leste + dx}
                  for indice, (dx, dy) in enumerate([(0.00001, 0.00001), (-0.00001, 0.00001),
                                                     (0.00001, -0.00001), (-0.00001, -0.00001)])]
        self.conferirConsulta(pontos, norte, leste, 0.01)
        self.assertEqual(len(MotorBusca(pontos).consultar(norte, leste, 0.01)["entregadores"]), 4)

    def testAntimeridianoEPolos(self):
        pontos = [{"id": 1, "latitude": 0, "longitude": -179.999},
                  {"id": 2, "latitude": 0, "longitude": 179.999},
                  {"id": 3, "latitude": 89.999, "longitude": 120}]
        self.conferirConsulta(pontos, 0, 180, 1)
        self.conferirConsulta(pontos, 89.999, 0, 1)

    def testVazioDuplicataETempo(self):
        self.assertEqual(MotorBusca([]).consultar(0, 0, 2)["entregadores"], [])
        pontos = [{"id": 1, "latitude": 0, "longitude": 0.01}]
        resultado = MotorBusca(pontos).consultar(0, 0, 2, 30)["entregadores"][0]
        self.assertAlmostEqual(resultado["tempoMin"], resultado["distanciaKm"] * 2)
        with self.assertRaises(ValueError):
            MotorBusca(pontos * 2)


class TestRuasESimulacao(unittest.TestCase):
    def testProjecaoSegmento(self):
        self.assertEqual(projetarNoSegmento((1, 2), (0, 0), (3, 0)), ((1, 0), 2))
        self.assertEqual(projetarNoSegmento((4, 0), (0, 0), (3, 0)), ((3, 0), 1))
        self.assertEqual(projetarNoSegmento((0, 2), (0, 0), (0, 0)), ((0, 0), 2))

    def testGradeContraTodosOsSegmentos(self):
        sorteador = random.Random(22)
        linhas = [[paraCoordenadas(sorteador.uniform(-3, 3), sorteador.uniform(-3, 3)) for _ in range(2)]
                  for _ in range(80)]
        malha = MalhaViaria(linhas)
        for _ in range(100):
            ponto = sorteador.uniform(-4, 4), sorteador.uniform(-4, 4)
            latitude, longitude, distancia = malha.projetar(*paraCoordenadas(*ponto))
            esperado = min(projetarNoSegmento(ponto, *segmento)[1] for segmento in malha.segmentos)
            self.assertAlmostEqual(distancia, esperado, places=8)

    def testEquilibrioReprodutibilidadeEProjecao(self):
        centros = [{"id": indice, "latitude": -19.92 + indice * 0.001, "longitude": -43.94}
                   for indice in range(5)]
        malha = MalhaViaria([[[-19.96, -43.94], [-19.88, -43.94]]])
        frota = gerarEntregadores(103, centros, malha)
        self.assertEqual(frota, gerarEntregadores(103, centros, malha))
        contagem = Counter(item["centroId"] for item in frota)
        self.assertLessEqual(max(contagem.values()) - min(contagem.values()), 1)
        self.assertEqual(len(frota), 103)
        for item in frota:
            self.assertAlmostEqual(item["longitude"], -43.94)
        self.assertEqual(gerarEntregadores(0, centros, malha), [])
        self.assertEqual(len(gerarEntregadores(2, centros, malha)), 2)

    def testBuscaSemAcentos(self):
        self.assertEqual(normalizarTexto("São João"), "sao joao")


if __name__ == "__main__":
    unittest.main()
