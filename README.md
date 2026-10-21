# TP1 - Algoritmos II

Busca de entregadores em Belo Horizonte usando Geohash e Trie compacta.

**Relatório do trabalho:** [docs/relatorio.md](docs/relatorio.md)

## Execução

Python 3.12 ou superior (testado com 3.14).

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python app.py
```

Abra http://127.0.0.1:8050, escolha um restaurante e clique em **Gerar entregadores**. A busca filtra a lista e limpa a seleção anterior; escolha um resultado para consultar. O raio e a velocidade podem ser alterados depois.

Se `data/ruas.json` ainda não existir, execute antes:

```powershell
.\.venv\Scripts\python scripts/baixarRuas.py
```

A malha de ruas já acompanha o projeto. Só é necessário baixá-la se o arquivo for removido. O mapa de fundo precisa de internet. No Linux, use `.venv/bin/python` no lugar de `.\.venv\Scripts\python`.

## Arquivos

- `app.py` e `assets/`: interface e estilo.
- `src/`: Geohash, Trie, busca, geometria, dados e simulação.
- `data/`: base de bares, coordenadas e malha viária.
- `scripts/`: preparação dos dados, experimentos e teste da interface.
- `tests/`: testes dos algoritmos e dos dados.
- `docs/`: [relatório](docs/relatorio.md), resultados e capturas usadas no relatório.

## Dados

O arquivo do enunciado tem 20.859 bares, mas não contém coordenadas. O cruzamento com a [base da PBH](https://dados.pbh.gov.br/pt_BR/dataset/atividade-economica/resource/108d887f-714b-4969-9a37-b959717bac7a) localizou 20.541 deles. Os outros 318 ficaram sem correspondência.

Para refazer a importação, informe o caminho do CSV da PBH:

```powershell
.\.venv\Scripts\python scripts/importarCoordenadas.py --origem "C:\caminho\dadosAtividadesEconomicas.csv"
```

O script salva `data/coordenadas.csv` e exibe o resumo no terminal. Para também salvar o resumo e a lista de pendências, acrescente `--relatorios "C:\caminho\relatorios"`.

Os `_id` das duas bases não correspondem. O script cruza nome, endereço, complemento, bairro e CNAE, e converte EPSG:31983 para latitude/longitude. Reinicie o app após importar.

As posições dos entregadores seguem uma normal em torno dos restaurantes e são projetadas sobre ruas do OpenStreetMap. A semente permite repetir a simulação. O tempo estimado usa distância geodésica e velocidade constante, sem calcular rotas.

## Testes

```powershell
.\.venv\Scripts\python -m unittest discover -s tests -v
.\.venv\Scripts\python scripts/experimentos.py
```

Os experimentos salvam os tempos em `docs/experimentos.csv` e comparam as consultas com busca exaustiva. Para executar o aplicativo, os testes dos algoritmos e os experimentos, basta instalar `requirements.txt`.

O `requirements-dev.txt` é opcional: inclui as dependências principais e adiciona Playwright para automatizar o navegador e gerar screenshots. Para esse teste, é necessário ter o Google Chrome instalado:

```powershell
.\.venv\Scripts\python -m pip install -r requirements-dev.txt
.\.venv\Scripts\python scripts/testarInterface.py
```

O app deve estar aberto para esse último teste.
