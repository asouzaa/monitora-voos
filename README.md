# Monitor de Voos saindo de Belém

Programa em Python para monitorar e comparar preços de ida e volta saindo de
Belém (`BEL`) para seis destinos:

- Recife (`REC`);
- Fortaleza (`FOR`);
- Maceió (`MCZ`);
- Natal (`NAT`);
- Rio de Janeiro (`RIO`);
- João Pessoa (`JPA`).

Todos os destinos usam estas combinações:

- `29/12/2026` a `06/01/2027`;
- `29/12/2026` a `07/01/2027`;
- `30/12/2026` a `06/01/2027`;
- `30/12/2026` a `07/01/2027`;
- `29/12/2026` a `05/01/2027`;
- `30/12/2026` a `08/01/2027`.

O monitor coleta resultados públicos do Google Voos por web scraping e registra
os preços de cada destino em uma planilha independente. Não exige conta, chave
de API ou serviço pago.

## Instalação

Requer Python 3.11 ou mais recente.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Uso

Executar uma consulta imediata para Recife, que continua sendo o destino padrão:

```bash
python -m monitora_voo executar
```

Consultar outro destino:

```bash
python -m monitora_voo executar --destino FOR
python -m monitora_voo executar --destino MCZ
python -m monitora_voo executar --destino NAT
python -m monitora_voo executar --destino RIO
python -m monitora_voo executar --destino JPA
```

Monitorar a cada 6 horas:

```bash
python -m monitora_voo monitorar --destino REC --intervalo-horas 6
```

O comando `monitorar` precisa permanecer em execução. Pressione `Ctrl+C` para
interromper.

## Painel web

O painel estático fica em `docs/`. A página inicial compara os seis destinos e
as páginas de análise exibem histórico, métricas e ofertas de cada rota. Para
visualizá-lo localmente:

```bash
python -m http.server 8000 --directory docs
```

Depois, acesse `http://localhost:8000`.

Para atualizar manualmente os arquivos do painel:

```bash
python -m monitora_voo exportar \
  --destino REC \
  --planilha monitoramento_voos.xlsx \
  --saida docs/dados.json

python -m monitora_voo exportar \
  --destino FOR \
  --planilha monitoramento_fortaleza.xlsx \
  --saida docs/dados_fortaleza.json
```

Os demais destinos seguem o mesmo formato e possuem caminhos padrão próprios,
portanto também podem ser exportados apenas com `--destino`.

## GitHub

O workflow `.github/workflows/monitorar.yml`:

- executa automaticamente a cada 6 horas, no horário de Belém;
- também pode ser iniciado manualmente pela aba `Actions`;
- consulta os seis destinos separadamente;
- salva um JSON e uma planilha para cada destino;
- publica o conteúdo de `docs/` no GitHub Pages.

Depois de enviar o projeto para um repositório público, abra `Settings → Pages`
e escolha `GitHub Actions` como origem da publicação. Em seguida, execute
`Monitorar voos e publicar painel` uma vez pela aba `Actions`.

O endereço será:

```text
https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/
```

## Planilha

Cada destino possui sua própria planilha, com duas abas:

- `Consultas`: uma linha por oferta de ida e volta retornada.
- `Resumo`: menor preço histórico, menor preço da última consulta, data da
  última consulta, quantidade de ofertas vistas e status.

`queda_detectada` fica como `sim` quando o menor preço da consulta atual for
menor que o menor preço histórico anterior, inclusive uma redução de R$ 0,01.
O histórico original em `docs/monitoramento_voos.xlsx` continua pertencendo a
Recife. Os demais destinos usam arquivos identificados pelo nome da cidade.
Para o Rio de Janeiro, a mesma análise combina ofertas do Galeão (`GIG`) e do
Santos Dumont (`SDU`).

## Limitações

O scraping depende da página pública do Google Voos. Alterações no site,
indisponibilidade temporária ou bloqueio de automação podem interromper uma
consulta. Nesse caso, o erro é salvo na aba `Resumo` sem apagar o histórico.

Os valores são informativos e podem mudar até a confirmação no site de venda.
O programa não compra passagens.

## Testes

```bash
python -m unittest discover
```
