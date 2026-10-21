import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.dados import raizProjeto


def baixarRuas(destino, endpoint):
    consulta = '''[out:json][timeout:180];
    way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|living_street|service|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link)$"]
    ["access"!~"^(private|no)$"]["motor_vehicle"!~"^(private|no)$"]["motorcar"!~"^(private|no)$"]
    ["service"!~"^(parking_aisle|driveway)$"](-20.06,-44.06,-19.75,-43.85);
    out geom;'''
    requisicao = Request(endpoint, data=urlencode({"data": consulta}).encode(),
                         headers={"User-Agent": "Alg2-TP1-BH/1.0 (academic local road simulator)"})
    with urlopen(requisicao, timeout=240) as resposta:
        dados = json.load(resposta)
    if dados.get("remark"):
        raise RuntimeError(f"Overpass devolveu erro ou resultado parcial: {dados['remark']}")
    linhas = [[[ponto["lat"], ponto["lon"]] for ponto in via["geometry"]]
              for via in dados.get("elements", []) if len(via.get("geometry", [])) >= 2]
    if not linhas:
        raise ValueError("A consulta não retornou vias. O cache anterior foi preservado.")
    resultado = {"fonte": "© OpenStreetMap contributors, ODbL 1.0", "endpoint": endpoint,
                 "obtidoEm": datetime.now(timezone.utc).isoformat(), "consulta": consulta,
                 "linhas": linhas}
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporario = destino.with_suffix(".tmp")
    temporario.write_text(json.dumps(resultado, ensure_ascii=False), encoding="utf-8")
    temporario.replace(destino)
    print(f"Salvas {len(linhas)} vias em {destino}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", default="https://overpass-api.de/api/interpreter")
    parser.add_argument("--destino", type=Path, default=raizProjeto / "data/ruas.json")
    argumentos = parser.parse_args()
    baixarRuas(argumentos.destino, argumentos.endpoint)
