const formatoMoeda = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
  maximumFractionDigits: 2,
});

const formatoConsulta = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short",
  timeStyle: "short",
  timeZone: "America/Belem",
});

const destinos = {
  REC: { arquivo: "./dados.json", nome: "Recife" },
  FOR: { arquivo: "./dados_fortaleza.json", nome: "Fortaleza" },
  MCZ: { arquivo: "./dados_maceio.json", nome: "Maceió" },
  NAT: { arquivo: "./dados_natal.json", nome: "Natal" },
  RIO: { arquivo: "./dados_rio.json", nome: "Rio de Janeiro" },
  JPA: { arquivo: "./dados_joao_pessoa.json", nome: "João Pessoa" },
};

document
  .querySelector("#botao-atualizar")
  .addEventListener("click", () => carregarComparacao());

carregarComparacao();
setInterval(carregarComparacao, 5 * 60 * 1000);

async function carregarComparacao() {
  const botao = document.querySelector("#botao-atualizar");
  botao.classList.add("carregando");
  botao.disabled = true;

  const resultados = await Promise.all(
    Object.entries(destinos).map(async ([codigo, configuracao]) => {
      try {
        const resposta = await fetch(`${configuracao.arquivo}?v=${Date.now()}`, {
          cache: "no-store",
        });
        if (!resposta.ok) {
          throw new Error(`Resposta HTTP ${resposta.status}`);
        }
        return [codigo, await resposta.json()];
      } catch (erro) {
        console.error(`Falha ao carregar ${codigo}:`, erro);
        return [codigo, null];
      }
    }),
  );

  const dadosPorDestino = Object.fromEntries(resultados);
  Object.entries(dadosPorDestino).forEach(([codigo, dados]) => {
    renderizarDestino(codigo, dados);
  });
  renderizarResultado(dadosPorDestino);

  botao.classList.remove("carregando");
  botao.disabled = false;
}

function renderizarDestino(codigo, dados) {
  const cartao = document.querySelector(`[data-destino="${codigo}"]`);
  const preco = cartao.querySelector('[data-campo="preco-atual"]');
  const recorde = cartao.querySelector('[data-campo="recorde"]');
  const consulta = cartao.querySelector('[data-campo="ultima-consulta"]');
  const listaDatas = cartao.querySelector('[data-campo="datas-vencedoras"]');

  cartao.classList.toggle("cartao-indisponivel", !dados);
  if (!dados) {
    preco.textContent = "Sem dados";
    recorde.textContent = "—";
    consulta.textContent = "Não foi possível carregar este destino";
    listaDatas.innerHTML = "<p>Combinações indisponíveis.</p>";
    return;
  }

  preco.textContent = formatarPreco(dados.resumo.ultimo_menor_preco);
  recorde.textContent = formatarPreco(dados.resumo.menor_preco_historico);
  consulta.textContent = dados.resumo.data_ultima_consulta_bem_sucedida
    ? `Consulta em ${formatarConsulta(dados.resumo.data_ultima_consulta_bem_sucedida)}`
    : "Aguardando primeira consulta válida";

  const datasVencedoras = dados.datas_vencedoras || [];
  if (!datasVencedoras.length) {
    listaDatas.innerHTML = "<p>Nenhuma data com preço disponível.</p>";
    return;
  }
  listaDatas.innerHTML = datasVencedoras
    .map(
      (periodo) => `
        <p>
          <strong>${formatarData(periodo.data_ida)} → ${formatarData(periodo.data_volta)}</strong>
          <span>${formatarPreco(periodo.menor_preco)}</span>
        </p>
      `,
    )
    .join("");
}

function renderizarResultado(dadosPorDestino) {
  const resultado = document.querySelector("#resultado-comparacao");
  const estado = document.querySelector("#estado-comparacao");
  const precos = Object.fromEntries(
    Object.entries(dadosPorDestino).map(([codigo, dados]) => [
      codigo,
      dados?.resumo?.ultimo_menor_preco ?? null,
    ]),
  );

  limparVencedores();
  const codigos = Object.keys(destinos);
  const codigosComPreco = codigos.filter((codigo) => precos[codigo] != null);
  if (codigosComPreco.length !== codigos.length) {
    const quantidadeAusentes = codigos.length - codigosComPreco.length;
    resultado.querySelector("strong").textContent = "Comparação indisponível";
    resultado.querySelector("small").textContent =
      `${quantidadeAusentes} destino${quantidadeAusentes === 1 ? " precisa" : "s precisam"} ter preço válido`;
    definirEstado(estado, "Dados incompletos", "alerta");
    return;
  }

  const menorPreco = Math.min(...codigos.map((codigo) => precos[codigo]));
  const vencedores = codigos.filter((codigo) => precos[codigo] === menorPreco);
  if (vencedores.length > 1) {
    resultado.querySelector("strong").textContent = "Empate";
    resultado.querySelector("small").textContent =
      `${vencedores.length} destinos estão em ${formatarPreco(menorPreco)}`;
    vencedores.forEach((codigo) => marcarVencedor(codigo, "Empate"));
    definirEstado(estado, "Preços empatados", "alerta");
    return;
  }

  const vencedor = vencedores[0];
  const segundoColocado = codigos
    .filter((codigo) => codigo !== vencedor)
    .sort((codigoA, codigoB) => precos[codigoA] - precos[codigoB])[0];
  const diferenca = precos[segundoColocado] - precos[vencedor];
  resultado.querySelector("strong").textContent = destinos[vencedor].nome;
  resultado.querySelector("small").textContent =
    `${formatarPreco(diferenca)} mais barato que ${destinos[segundoColocado].nome}`;
  marcarVencedor(vencedor, "Menor preço");
  definirEstado(estado, "Comparação atualizada", "normal");
}

function marcarVencedor(codigo, texto) {
  const cartao = document.querySelector(`[data-destino="${codigo}"]`);
  const selo = cartao.querySelector(".selo-vencedor");
  cartao.classList.add("cartao-vencedor");
  selo.textContent = texto;
  selo.hidden = false;
}

function limparVencedores() {
  document.querySelectorAll(".cartao-destino").forEach((cartao) => {
    cartao.classList.remove("cartao-vencedor");
    cartao.querySelector(".selo-vencedor").hidden = true;
  });
}

function definirEstado(elemento, texto, tipo) {
  elemento.textContent = texto;
  elemento.classList.toggle("estado-alerta", tipo === "alerta");
  elemento.classList.remove("estado-erro");
}

function formatarPreco(valor) {
  return valor == null ? "—" : formatoMoeda.format(valor);
}

function formatarConsulta(valor) {
  return formatoConsulta.format(new Date(valor));
}

function formatarData(valor) {
  const [ano, mes, dia] = valor.split("-").map(Number);
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
  })
    .format(new Date(ano, mes - 1, dia))
    .replace(".", "");
}
