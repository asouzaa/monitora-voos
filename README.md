# Monitor de Voos BEL ↔ REC

Programa em Python para monitorar preços de ida e volta entre Belém (`BEL`) e
Recife (`REC`) para estas combinações:

- `29/12/2026` a `06/01/2027`;
- `29/12/2026` a `07/01/2027`;
- `30/12/2026` a `06/01/2027`;
- `30/12/2026` a `07/01/2027`;
- `29/12/2026` a `05/01/2027`;
- `30/12/2026` a `08/01/2027`.

O monitor coleta resultados públicos do Google Voos por web scraping e registra
os preços em `monitoramento_voos.xlsx`. Não exige conta, chave de API ou serviço
pago.

## Instalação

Requer Python 3.11 ou mais recente.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

## Uso

Executar uma consulta imediata:

```bash
python -m monitora_voo executar
```

Monitorar a cada 6 horas:

```bash
python -m monitora_voo monitorar --intervalo-horas 6
```

O comando `monitorar` precisa permanecer em execução. Pressione `Ctrl+C` para
interromper.

## Painel web

O painel estático fica em `docs/` e lê os dados de `docs/dados.json`. Para
visualizá-lo localmente:

```bash
python -m http.server 8000 --directory docs
```

Depois, acesse `http://localhost:8000`.

Para atualizar manualmente o JSON do painel:

```bash
python -m monitora_voo exportar \
  --planilha monitoramento_voos.xlsx \
  --saida docs/dados.json
```

## GitHub

O workflow `.github/workflows/monitorar.yml`:

- executa automaticamente a cada 6 horas, no horário de Belém;
- também pode ser iniciado manualmente pela aba `Actions`;
- salva `docs/dados.json` e `docs/monitoramento_voos.xlsx`;
- publica o conteúdo de `docs/` no GitHub Pages.

Depois de enviar o projeto para um repositório público, abra `Settings → Pages`
e escolha `GitHub Actions` como origem da publicação. Em seguida, execute
`Monitorar voos e publicar painel` uma vez pela aba `Actions`.

O endereço será:

```text
https://SEU-USUARIO.github.io/NOME-DO-REPOSITORIO/
```

## Planilha

A planilha tem duas abas:

- `Consultas`: uma linha por oferta de ida e volta retornada.
- `Resumo`: menor preço histórico, menor preço da última consulta, data da
  última consulta, quantidade de ofertas vistas e status.

`queda_detectada` fica como `sim` quando o menor preço da consulta atual for
menor que o menor preço histórico anterior, inclusive uma redução de R$ 0,01.

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
