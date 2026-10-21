from functools import lru_cache
from time import perf_counter

import dash_leaflet as dl
from dash import Dash, Input, Output, State, dash_table, dcc, html, no_update

from src.busca import MotorBusca
from src.dados import carregarBares, carregarRestaurantes, normalizarTexto, raizProjeto
from src.ruas import MalhaViaria
from src.simulacao import gerarEntregadores

bares = carregarBares()
erroDados = ""
try:
    restaurantesReais = carregarRestaurantes(bares)
except (ValueError, KeyError) as erro:
    restaurantesReais = []
    erroDados = str(erro)

app = Dash(__name__, title="TP1 - Busca de entregadores", update_title="Consultando…")
server = app.server


@lru_cache(maxsize=1)
def carregarMalha():
    return MalhaViaria.carregar(raizProjeto / "data/ruas.json")


def campo(rotulo, componente):
    return html.Div([html.Label(rotulo, htmlFor=componente.id), componente], className="campo")


app.layout = html.Div([
    dcc.Store(id="frota", data=[]),
    html.Main([
        html.H1("TP1 - Busca de entregadores"),
        html.Div([
            html.Aside([
                html.Div(id="avisoBase", className="aviso", role="status"),
                campo("Buscar por nome, endereço ou bairro", dcc.Input(id="buscaTexto", type="search",
                      placeholder="Ex.: Savassi ou Avenida Portugal", debounce=False, value="")),
                campo("Restaurante", dcc.Dropdown(id="restaurante", placeholder="Selecione um restaurante", clearable=True)),
                html.Hr(),
                html.Div([
                    campo("Entregadores", dcc.Input(id="quantidade", type="number", min=0, max=10000, step=1, value=1000)),
                    campo("Semente", dcc.Input(id="semente", type="number", min=0, max=2147483647, step=1, value=42)),
                ], className="duasColunas"),
                campo("Dispersão da normal (km)", dcc.Input(id="desvio", type="number", min=0.05, max=5, step=0.05, value=0.7)),
                html.Button("Gerar entregadores", id="gerar", n_clicks=0, className="botaoPrincipal"),
                dcc.Loading(html.Div(id="statusFrota", role="status", className="ajuda")),
                html.Hr(),
                campo("Raio de atendimento (km)", dcc.Slider(id="raio", min=0.1, max=10, step=0.1, value=2,
                      marks={0.1: "0,1", 2: "2", 5: "5", 10: "10"}, tooltip={"placement": "bottom", "always_visible": True})),
                campo("Velocidade média (km/h)", dcc.Input(id="velocidade", type="number", min=1, max=100, value=25)),
            ], className="painel controles"),
            html.Section([
                html.Div(id="metricas", className="metricas", **{"aria-live": "polite"}),
                html.Div([
                    html.Div([html.Div([
                        html.Span("● Dentro do raio", className="legendaDentro"),
                        html.Span("● Fora do raio", className="legendaFora"),
                        html.Span("● Restaurante", className="legendaRestaurante")], className="legenda")], className="tituloMapa"),
                    dl.Map([dl.TileLayer(url="https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                                        attribution='© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'),
                            dl.LayerGroup(id="pontos")], id="mapa", center=[-19.925, -43.938], zoom=13,
                           preferCanvas=True, style={"height": "480px", "width": "100%"}),
                ], className="painel mapaPainel"),
                html.Div([
                    html.Div([html.H2("Entregadores disponíveis"), html.Button("Baixar CSV", id="exportar", n_clicks=0)], className="tituloMapa"),
                    html.P(id="resumoConsulta", className="ajuda", role="status"),
                    dash_table.DataTable(id="tabela", columns=[
                        {"name": "Entregador", "id": "id"}, {"name": "Distância (km)", "id": "distanciaKm", "type": "numeric"},
                        {"name": "Tempo estimado (min)", "id": "tempoMin", "type": "numeric"}],
                        data=[], page_size=8, sort_action="native", style_table={"overflowX": "auto"},
                        style_cell={"fontFamily": "Arial, sans-serif", "padding": "9px", "textAlign": "left", "border": "0"},
                        style_header={"backgroundColor": "#f3f6f6", "fontWeight": "600", "color": "#52626a"},
                        style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#fafcfc"}]),
                    dcc.Download(id="download"),
                ], className="painel resultados"),
            ], className="conteudo"),
        ], className="layout"),
    ]),
])


@app.callback(Output("restaurante", "options"), Output("restaurante", "value"), Output("avisoBase", "children"),
              Input("buscaTexto", "value"))
def atualizarRestaurantes(texto):
    restaurantes = restaurantesReais
    termo = normalizarTexto(texto or "")
    encontrados = [item for item in restaurantes if termo in normalizarTexto(
        f"{item['nome']} {item['endereco']} {item['bairro']}")]
    opcoes = [{"label": f"{item['nome']} · {item['endereco']} · {item['bairro']}", "value": item["id"]}
              for item in encontrados]
    aviso = f"{len(restaurantes)} bares com coordenadas."
    if not restaurantes:
        aviso += " Adicione data/coordenadas.csv e reinicie o app. " + erroDados
    return opcoes, None, aviso


@app.callback(Output("frota", "data"), Output("statusFrota", "children"),
              Input("gerar", "n_clicks"),
              State("quantidade", "value"), State("desvio", "value"), State("semente", "value"), prevent_initial_call=True)
def atualizarFrota(cliques, quantidade, desvio, semente):
    try:
        if quantidade is None or int(quantidade) != quantidade:
            raise ValueError("Informe uma quantidade inteira.")
        if semente is None or int(semente) != semente or not 0 <= semente <= 2147483647:
            raise ValueError("Informe uma semente inteira entre 0 e 2147483647.")
        if desvio is None:
            raise ValueError("Informe a dispersão.")
        inicio = perf_counter()
        frota = gerarEntregadores(int(quantidade), restaurantesReais, carregarMalha(), desvio, int(semente))
        return frota, f"{len(frota)} entregadores gerados em {perf_counter() - inicio:.2f} s."
    except FileNotFoundError:
        return no_update, "Malha ausente. Execute: python scripts/baixarRuas.py e tente novamente."
    except (ValueError, TypeError) as erro:
        return no_update, str(erro)


def cartao(valor, legenda):
    return html.Div([html.Strong(valor), html.Span(legenda)], className="metrica")


@app.callback(Output("pontos", "children"), Output("tabela", "data"), Output("metricas", "children"),
              Output("resumoConsulta", "children"), Output("mapa", "center"),
              Input("frota", "data"), Input("restaurante", "value"), Input("raio", "value"),
              Input("velocidade", "value"), Input("restaurante", "options"))
def atualizarConsulta(frota, restauranteId, raio, velocidade, opcoes):
    restaurante = next((item for item in restaurantesReais if item["id"] == restauranteId), None)
    metricasVazias = [cartao(len(frota), "na frota"), cartao("—", "no raio"), cartao("—", "menor distância"), cartao("—", "consulta")]
    if restaurante is None:
        mensagem = "Selecione um restaurante." if opcoes else "Nenhum restaurante encontrado."
        return [], [], metricasVazias, mensagem, no_update
    if velocidade is None or not 1 <= velocidade <= 100:
        return [], [], metricasVazias, "Informe uma velocidade entre 1 e 100 km/h.", no_update
    inicio = perf_counter()
    motor = MotorBusca(frota)
    indiceMs = (perf_counter() - inicio) * 1000
    resultado = motor.consultar(restaurante["latitude"], restaurante["longitude"], raio, velocidade)
    aprovados = {item["id"] for item in resultado["entregadores"]}
    pontos = []
    for item in frota:
        dentro = item["id"] in aprovados
        pontos.append(dl.CircleMarker(center=[item["latitude"], item["longitude"]], radius=5 if dentro else 3,
                       color="#df5b48" if dentro else "#98a4ad", weight=1, fill=True, fillOpacity=0.85 if dentro else 0.45,
                       children=dl.Tooltip(f"Entregador {item['id']} · {'dentro' if dentro else 'fora'} do raio")))
    centro = [restaurante["latitude"], restaurante["longitude"]]
    pontos.extend([dl.Circle(center=centro, radius=raio * 1000, color="#237d77", weight=2, fillOpacity=0.06),
                   dl.CircleMarker(center=centro, radius=10, color="white", weight=3, fill=True,
                                   fillColor="#176c66", fillOpacity=1, children=dl.Tooltip(restaurante["nome"]))])
    linhas = [{"id": item["id"], "distanciaKm": round(item["distanciaKm"], 3), "tempoMin": round(item["tempoMin"], 2)}
              for item in resultado["entregadores"]]
    menor = f"{linhas[0]['distanciaKm']:.3f} km" if linhas else "—"
    metricas = [cartao(len(frota), "na frota"), cartao(len(linhas), "no raio"), cartao(menor, "menor distância"),
                cartao(f"{resultado['consultaMs']:.2f} ms", "consulta")]
    resumo = (f"{resultado['candidatos']} candidatos · {len(resultado['prefixos'])} células · "
              f"índice: {indiceMs:.2f} ms")
    if not frota:
        resumo = "Clique em Gerar entregadores."
    elif not linhas:
        resumo = "Nenhum entregador dentro do raio. " + resumo
    return pontos, linhas, metricas, resumo, centro


@app.callback(Output("download", "data"), Input("exportar", "n_clicks"), State("tabela", "data"), prevent_initial_call=True)
def exportarTabela(cliques, linhas):
    import csv
    import io
    arquivo = io.StringIO(newline="")
    escritor = csv.DictWriter(arquivo, fieldnames=["id", "distanciaKm", "tempoMin"])
    escritor.writeheader()
    escritor.writerows(linhas)
    return {"content": arquivo.getvalue(), "filename": "entregadores.csv", "type": "text/csv"}


if __name__ == "__main__":
    from waitress import serve
    print("Interface disponível em http://127.0.0.1:8050", flush=True)
    serve(server, host="127.0.0.1", port=8050, threads=8)
