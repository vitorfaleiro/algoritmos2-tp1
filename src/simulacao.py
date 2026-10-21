from random import Random

from src.geometria import paraPlano, paraCoordenadas


def gerarEntregadores(quantidade, restaurantes, malha, desvioKm=0.7, semente=42):
    if not isinstance(quantidade, int) or not 0 <= quantidade <= 10000:
        raise ValueError("A quantidade deve ser um inteiro entre 0 e 10.000.")
    if not restaurantes:
        raise ValueError("Não há restaurantes com coordenadas disponíveis.")
    if not 0 < desvioKm <= 5:
        raise ValueError("O desvio deve estar entre 0 e 5 km, excluindo zero.")
    sorteador = Random(semente)
    centros = list(restaurantes)
    sorteador.shuffle(centros)
    entregadores = []
    for indice in range(quantidade):
        centro = centros[indice % len(centros)]
        x, y = paraPlano(centro["latitude"], centro["longitude"])
        latitude, longitude = paraCoordenadas(sorteador.gauss(x, desvioKm), sorteador.gauss(y, desvioKm))
        latitude, longitude, deslocamento = malha.projetar(latitude, longitude)
        entregadores.append({"id": indice + 1, "latitude": latitude, "longitude": longitude,
                             "centroId": centro["id"], "correcaoKm": deslocamento})
    return entregadores
