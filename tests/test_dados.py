import unittest

from scripts.importarCoordenadas import chaveEstabelecimento, camposChave
from src.dados import carregarBares, carregarRestaurantes


class TestDados(unittest.TestCase):
    def testChaveNaoDependeDoId(self):
        linha = {campo: "X" for campo in camposChave}
        self.assertEqual(chaveEstabelecimento({**linha, "_id": "1"}),
                         chaveEstabelecimento({**linha, "_id": "999"}))
        self.assertNotEqual(chaveEstabelecimento(linha), chaveEstabelecimento({**linha, "NUMERO_IMOVEL": "2"}))

    def testBaseRealImportada(self):
        bares = carregarBares()
        self.assertEqual(len(bares), 20859)
        restaurantes = carregarRestaurantes(bares)
        if not restaurantes:
            self.skipTest("Execute a importação para verificar a base complementar.")
        self.assertEqual(len({item["id"] for item in restaurantes}), len(restaurantes))
        for item in restaurantes:
            self.assertTrue(-20.1 < item["latitude"] < -19.7)
            self.assertTrue(-44.1 < item["longitude"] < -43.8)

    def testCrsPbh(self):
        from pyproj import Transformer
        longitude, latitude = Transformer.from_crs(31983, 4326, always_xy=True).transform(611489.04, 7799534.51)
        self.assertTrue(-20 < latitude < -19.8 and -44 < longitude < -43.8)


if __name__ == "__main__":
    unittest.main()
