import json
from pathlib import Path

from playwright.sync_api import sync_playwright

raizProjeto = Path(__file__).resolve().parents[1]


def testarInterface():
    destino = raizProjeto / "docs/screenshots"
    destino.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        print("Abrindo Chrome headless...", flush=True)
        navegador = playwright.chromium.launch(channel="chrome", headless=True, args=["--no-proxy-server"])
        pagina = navegador.new_page(viewport={"width": 1440, "height": 1100}, device_scale_factor=1)
        erros = []
        pagina.on("pageerror", lambda erro: erros.append(str(erro)))
        pagina.on("pageerror", lambda erro: print("Erro JS:", erro, flush=True))
        pagina.on("console", lambda mensagem: print("Console:", mensagem.text, flush=True) if mensagem.type == "error" else None)
        pagina.on("requestfailed", lambda pedido: print("Falha HTTP:", pedido.url, pedido.failure, flush=True))
        print("Carregando app...", flush=True)
        pagina.goto("http://127.0.0.1:8050", wait_until="domcontentloaded")
        print("Documento carregado; aguardando controles...", flush=True)
        pagina.wait_for_function("document.querySelector('#resumoConsulta')?.textContent.includes('Selecione um restaurante')")
        pagina.locator("#restaurante").click()
        pagina.get_by_text("BAR E CAFE DONATELO LTDA", exact=False).click()
        pagina.wait_for_function("document.querySelector('#resumoConsulta').textContent.includes('Clique em Gerar')")
        pagina.get_by_role("button", name="Gerar entregadores").click()
        pagina.wait_for_timeout(2500)
        print("Estado da frota:", pagina.locator("#statusFrota").inner_text(), flush=True)
        pagina.wait_for_function("document.querySelector('#statusFrota').textContent.includes('gerados em')", timeout=120000)
        pagina.wait_for_function("document.querySelector('#resumoConsulta').textContent.includes('candidatos')", timeout=120000)
        pagina.screenshot(path=str(destino / "01-consulta.png"), full_page=True)
        print("Consulta inicial:", pagina.locator("#resumoConsulta").inner_text())
        pagina.locator("#buscaTexto").fill("PORTUGAL")
        pagina.locator("#buscaTexto").press("Tab")
        pagina.wait_for_function("document.querySelector('#resumoConsulta').textContent.includes('Selecione um restaurante')")
        assert pagina.locator('#tabela td[data-dash-column="id"]').count() == 0
        pagina.locator("#restaurante").click()
        pagina.get_by_text("BAR E CAFE DONATELO LTDA", exact=False).click()
        pagina.wait_for_function("document.querySelector('#resumoConsulta').textContent.includes('candidatos')")
        pagina.screenshot(path=str(destino / "02-busca-endereco.png"), full_page=True)
        pagina.locator("#quantidade").fill("30")
        pagina.get_by_role("button", name="Gerar entregadores").click()
        pagina.wait_for_function("document.querySelector('#statusFrota').textContent.startsWith('30 entregadores')", timeout=120000)
        pagina.wait_for_function("document.querySelector('#metricas').textContent.startsWith('30')", timeout=120000)
        with pagina.expect_download() as download:
            pagina.get_by_role("button", name="Baixar CSV").click()
        assert download.value.suggested_filename == "entregadores.csv"
        pagina.locator("#quantidade").fill("0")
        pagina.get_by_role("button", name="Gerar entregadores").click()
        pagina.wait_for_function("document.querySelector('#statusFrota').textContent.startsWith('0 entregadores')", timeout=120000)
        pagina.wait_for_function("document.querySelector('#metricas').textContent.startsWith('0')", timeout=120000)
        pagina.locator("#buscaTexto").fill("zzzz-sem-restaurante")
        pagina.locator("#buscaTexto").press("Tab")
        pagina.wait_for_function("document.querySelector('#resumoConsulta').textContent.includes('Nenhum restaurante')")
        pagina.set_viewport_size({"width": 390, "height": 844})
        pagina.wait_for_timeout(1500)
        pagina.screenshot(path=str(destino / "03-mobile-vazio.png"), full_page=True)
        assert pagina.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), "Overflow horizontal no celular"
        assert not erros, erros
        print(json.dumps({"errosJavascript": erros, "testes": ["geração", "busca", "substituição", "CSV", "frota vazia", "busca vazia", "mobile"]}))
        navegador.close()


if __name__ == "__main__":
    testarInterface()
