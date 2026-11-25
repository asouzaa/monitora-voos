const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const { test } = require("node:test");
const { runInNewContext } = require("node:vm");

function prepararPainel() {
  const elementos = new Map();
  function obterElemento(seletor) {
    if (!elementos.has(seletor)) {
      elementos.set(seletor, {
        textContent: "",
        classList: { add() {}, remove() {}, toggle() {} },
        addEventListener() {},
        querySelector: (filho) => obterElemento(`${seletor} ${filho}`),
      });
    }
    return elementos.get(seletor);
  }
  const contexto = {
    document: { querySelector: obterElemento, querySelectorAll: () => [] },
    fetch: () => new Promise(() => {}),
    setInterval() {},
  };
  runInNewContext(readFileSync(`${__dirname}/../docs/comparacao.js`, "utf8"), contexto);
  return { renderizar: contexto.renderizarResultado, obterElemento };
}

test("compara destinos com preço mesmo quando São Paulo ainda está sem ofertas", () => {
  const painel = prepararPainel();
  painel.renderizar({
    REC: { resumo: { ultimo_menor_preco: 1753 } },
    FOR: { resumo: { ultimo_menor_preco: 1596 } },
    SAO: { resumo: { ultimo_menor_preco: null } },
  });
  assert.equal(painel.obterElemento("#resultado-comparacao strong").textContent, "Fortaleza");
  assert.equal(painel.obterElemento("#estado-comparacao").textContent, "Comparação parcial");
  assert.match(painel.obterElemento("#resultado-comparacao small").textContent, /2 de 7/);
});

test("exibe o único destino com preço sem calcular diferença inexistente", () => {
  const painel = prepararPainel();
  painel.renderizar({ SAO: { resumo: { ultimo_menor_preco: 1268 } } });
  assert.equal(painel.obterElemento("#resultado-comparacao strong").textContent, "São Paulo");
  assert.match(painel.obterElemento("#resultado-comparacao small").textContent, /1 de 7/);
  assert.doesNotMatch(painel.obterElemento("#resultado-comparacao small").textContent, /NaN|undefined/);
});

test("aguarda preços quando nenhum destino tem ofertas", () => {
  const painel = prepararPainel();
  painel.renderizar({ SAO: null });
  assert.equal(painel.obterElemento("#resultado-comparacao strong").textContent, "Aguardando preços");
});

test("compara os sete destinos e reconhece empates", () => {
  const painel = prepararPainel();
  const dados = Object.fromEntries(
    ["REC", "FOR", "MCZ", "NAT", "RIO", "JPA", "SAO"].map((codigo, indice) => [
      codigo, { resumo: { ultimo_menor_preco: 1000 + indice * 100 } },
    ]),
  );
  painel.renderizar(dados);
  assert.equal(painel.obterElemento("#resultado-comparacao strong").textContent, "Recife");
  assert.equal(painel.obterElemento("#estado-comparacao").textContent, "Comparação atualizada");
  dados.SAO.resumo.ultimo_menor_preco = 1000;
  painel.renderizar(dados);
  assert.equal(painel.obterElemento("#resultado-comparacao strong").textContent, "Empate");
  assert.equal(painel.obterElemento("#estado-comparacao").textContent, "Preços empatados");
});
