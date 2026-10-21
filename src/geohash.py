from math import asin, cos, degrees, floor, radians, sin

from src.geometria import raioTerraKm, validarCoordenadas

alfabeto = "0123456789bcdefghjkmnpqrstuvwxyz"


def codificarGeohash(latitude, longitude, precisao=8):
    validarCoordenadas(latitude, longitude)
    if not isinstance(precisao, int) or not 1 <= precisao <= 8:
        raise ValueError("A precisão deve ser um inteiro entre 1 e 8.")
    limites = [[-180.0, 180.0], [-90.0, 90.0]]
    coordenadas = [longitude, latitude]
    resultado = []
    valor = 0
    for indiceBit in range(precisao * 5):
        eixo = indiceBit % 2  # O primeiro bit sempre pertence à longitude.
        meio = sum(limites[eixo]) / 2
        bit = int(coordenadas[eixo] >= meio)
        limites[eixo][1 - bit] = meio
        valor = (valor << 1) | bit
        if indiceBit % 5 == 4:
            resultado.append(alfabeto[valor])
            valor = 0
    return "".join(resultado)


def decodificarLimites(prefixo):
    if len(prefixo) > 8 or any(letra not in alfabeto for letra in prefixo):
        raise ValueError("Prefixo Geohash inválido.")
    limites = [[-180.0, 180.0], [-90.0, 90.0]]
    indiceBit = 0
    for letra in prefixo:
        valor = alfabeto.index(letra)
        for deslocamento in range(4, -1, -1):
            eixo = indiceBit % 2
            bit = (valor >> deslocamento) & 1
            limites[eixo][1 - bit] = sum(limites[eixo]) / 2
            indiceBit += 1
    return (*limites[1], *limites[0])  # sul, norte, oeste, leste


def cobrirRaio(latitude, longitude, raioKm):
    """Cobre o retângulo do raio, ajustando a precisão das células."""
    validarCoordenadas(latitude, longitude)
    if not 0 <= raioKm <= 1000:
        raise ValueError("O raio deve estar entre 0 e 1000 km.")
    angulo = raioKm / raioTerraKm
    sul = max(-90, latitude - degrees(angulo))
    norte = min(90, latitude + degrees(angulo))
    if sul <= -90 or norte >= 90:
        intervalosLongitude = [(-180, 180)]
    else:
        deltaLongitude = degrees(asin(min(1, sin(angulo) / cos(radians(latitude)))))
        oeste, leste = longitude - deltaLongitude, longitude + deltaLongitude
        if oeste < -180:
            intervalosLongitude = [(-180, leste), (oeste + 360, 180)]
        elif leste > 180:
            intervalosLongitude = [(oeste, 180), (-180, leste - 360)]
        else:
            intervalosLongitude = [(oeste, leste)]

    for precisao in range(8, 0, -1):
        bitsLongitude = (5 * precisao + 1) // 2
        bitsLatitude = (5 * precisao) // 2
        largura = 360 / (2 ** bitsLongitude)
        altura = 180 / (2 ** bitsLatitude)
        linhaInicial = max(0, floor((sul + 90) / altura))
        linhaFinal = min(2 ** bitsLatitude - 1, floor((norte + 90) / altura))
        faixas = []
        for oeste, leste in intervalosLongitude:
            colunaInicial = max(0, floor((oeste + 180) / largura))
            colunaFinal = min(2 ** bitsLongitude - 1, floor((leste + 180) / largura))
            faixas.append((colunaInicial, colunaFinal))
        quantidade = (linhaFinal - linhaInicial + 1) * sum(b - a + 1 for a, b in faixas)
        if quantidade <= 64 or precisao == 1:
            break

    prefixos = set()
    for linha in range(linhaInicial, linhaFinal + 1):
        for colunaInicial, colunaFinal in faixas:
            for coluna in range(colunaInicial, colunaFinal + 1):
                prefixos.add(codificarGeohash(-90 + (linha + 0.5) * altura,
                                             -180 + (coluna + 0.5) * largura, precisao))
    return sorted(prefixos)
