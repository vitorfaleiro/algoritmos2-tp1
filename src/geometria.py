from math import asin, cos, degrees, hypot, isfinite, radians, sin, sqrt

raioTerraKm = 6371.0088
latitudeReferencia = -19.92
longitudeReferencia = -43.94


def validarCoordenadas(latitude, longitude):
    if not isfinite(latitude) or not isfinite(longitude):
        raise ValueError("As coordenadas precisam ser finitas.")
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise ValueError("Latitude ou longitude fora do intervalo permitido.")


def distanciaKm(latitudeA, longitudeA, latitudeB, longitudeB):
    """Haversine: distância em linha geodésica, não percurso pelas ruas."""
    deltaLatitude = radians(latitudeB - latitudeA)
    deltaLongitude = radians(longitudeB - longitudeA)
    valor = (sin(deltaLatitude / 2) ** 2
             + cos(radians(latitudeA)) * cos(radians(latitudeB))
             * sin(deltaLongitude / 2) ** 2)
    return 2 * raioTerraKm * asin(sqrt(min(1, max(0, valor))))


def paraPlano(latitude, longitude):
    # Aproximação equiretangular local em km, adequada à escala de BH.
    x = raioTerraKm * radians(longitude - longitudeReferencia) * cos(radians(latitudeReferencia))
    y = raioTerraKm * radians(latitude - latitudeReferencia)
    return x, y


def paraCoordenadas(x, y):
    latitude = latitudeReferencia + degrees(y / raioTerraKm)
    longitude = longitudeReferencia + degrees(x / (raioTerraKm * cos(radians(latitudeReferencia))))
    return latitude, longitude


def projetarNoSegmento(ponto, inicio, fim):
    dx, dy = fim[0] - inicio[0], fim[1] - inicio[1]
    tamanhoQuadrado = dx * dx + dy * dy
    if tamanhoQuadrado == 0:
        return inicio, hypot(ponto[0] - inicio[0], ponto[1] - inicio[1])
    fator = ((ponto[0] - inicio[0]) * dx + (ponto[1] - inicio[1]) * dy) / tamanhoQuadrado
    fator = min(1, max(0, fator))
    projecao = inicio[0] + fator * dx, inicio[1] + fator * dy
    return projecao, hypot(ponto[0] - projecao[0], ponto[1] - projecao[1])
