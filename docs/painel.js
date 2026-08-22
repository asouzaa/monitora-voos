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

let historicoAtual = [];
let coordenadasGrafico = [];

const rotasDisponiveis = {
  REC: { arquivoDados: "./dados.json", nome: "Recife" },
  FOR: { arquivoDados: "./dados_fortaleza.json", nome: "Fortaleza" },
  MCZ: { arquivoDados: "./dados_maceio.json", nome: "Maceió" },
  NAT: { arquivoDados: "./dados_natal.json", nome: "Natal" },
  RIO: { arquivoDados: "./dados_rio.json", nome: "Rio de Janeiro" },
  JPA: { arquivoDados: "./dados_joao_pessoa.json", nome: "João Pessoa" },
};
const parametroDestino = new URLSearchParams(window.location.search)
  .get("destino")
  ?.toUpperCase();
const codigoDestino = parametroDestino in rotasDisponiveis ? parametroDestino : "REC";
const rotaSelecionada = rotasDisponiveis[codigoDestino];

document
  .querySelector("#botao-atualizar")
  .addEventListener("click", () => carregarDados());
window.addEventListener("resize", () => desenharGrafico(historicoAtual));

configurarLinkGitHub();
configurarInteracaoGrafico();
carregarDados();
setInterval(carregarDados, 5 * 60 * 1000);

async function carregarDados() {
  const botao = document.querySelector("#botao-atualizar");
  botao.classList.add("carregando");
  botao.disabled = true;

  try {
    const resposta = await fetch(`${rotaSelecionada.arquivoDados}?v=${Date.now()}`, {
      cache: "no-store",
    });
    if (!resposta.ok) {
      throw new Error(`Resposta HTTP ${resposta.status}`);
    }
    const dados = await resposta.json();
    renderizar(dados);
  } catch (erro) {
    definirEstado("Falha ao carregar", "erro");
    document.querySelector("#situacao").textContent = "Dados indisponíveis";
    document.querySelector("#gerado-em").textContent =
      "Tente atualizar novamente em alguns instantes";
    console.error(erro);
  } finally {
    botao.classList.remove("carregando");
    botao.disabled = false;
  }
}

function renderizar(dados) {
  const { rota, resumo, ofertas = [], historico = [], planilha } = dados;
  historicoAtual = historico;

  document.title = `Radar BEL ↔ ${rota.destino} · ${rota.nome_destino}`;
  document.querySelector("#marca-destino").textContent =
    `Belém ↔ ${rota.nome_destino}`;

  document.querySelector("#origem").textContent = rota.origem;
  document.querySelector("#destino").textContent = rota.destino;
  document.querySelector("#periodos-monitorados").textContent =
    rota.periodos.map(formatarPeriodo).join(" · ");
  document.querySelector("#passageiros").textContent =
    `${rota.adultos} adulto${rota.adultos === 1 ? "" : "s"} · Econômica`;

  document.querySelector("#preco-atual").textContent = formatarPreco(
    resumo.ultimo_menor_preco,
  );
  document.querySelector("#menor-historico").textContent = formatarPreco(
    resumo.menor_preco_historico,
  );
  document.querySelector("#total-ofertas").textContent =
    resumo.quantidade_ofertas_vistas.toLocaleString("pt-BR");
  document.querySelector("#ultima-consulta").textContent =
    resumo.data_ultima_consulta_bem_sucedida
      ? `Consulta em ${formatarConsulta(resumo.data_ultima_consulta_bem_sucedida)}`
      : "Aguardando primeira consulta";
  document.querySelector("#gerado-em").textContent =
    `Painel atualizado em ${formatarConsulta(dados.gerado_em)}`;

  atualizarSituacao(resumo.status);
  atualizarPlanilha(planilha);
  renderizarOfertas(ofertas);
  desenharGrafico(historico);
}

function formatarPeriodo(periodo) {
  return `${formatarDataNumerica(periodo.data_ida)} → ${formatarDataNumerica(periodo.data_volta)}`;
}

function formatarDataNumerica(valor) {
  return valor.split("-").reverse().join("/");
}

function atualizarSituacao(status) {
  const situacao = document.querySelector("#situacao");
  if (status === "queda detectada") {
    situacao.textContent = "Preço caiu";
    definirEstado("Queda detectada", "alerta");
    return;
  }
  if (status.startsWith("erro:")) {
    situacao.textContent = "Consulta com erro";
    definirEstado("Requer atenção", "erro");
    return;
  }
  if (status === "sem ofertas") {
    situacao.textContent = "Sem ofertas";
    definirEstado("Consulta concluída", "alerta");
    return;
  }
  if (status === "sem consultas") {
    situacao.textContent = "Aguardando";
    definirEstado("Ainda sem dados", "alerta");
    return;
  }
  situacao.textContent = "Sem nova queda";
  definirEstado("Monitor ativo", "normal");
}

function definirEstado(texto, tipo) {
  const estado = document.querySelector("#estado-monitor");
  estado.textContent = texto;
  estado.classList.toggle("estado-alerta", tipo === "alerta");
  estado.classList.toggle("estado-erro", tipo === "erro");
}

function atualizarPlanilha(planilha) {
  const link = document.querySelector("#link-planilha");
  link.hidden = !planilha?.disponivel;
  if (planilha?.disponivel) {
    link.href = `./${planilha.arquivo}`;
  }
}

function renderizarOfertas(ofertas) {
  const corpo = document.querySelector("#lista-ofertas");
  const quantidade = ofertas.length;
  document.querySelector("#quantidade-ofertas").textContent =
    `${quantidade} oferta${quantidade === 1 ? "" : "s"}`;

  if (!quantidade) {
    corpo.innerHTML =
      '<tr><td colspan="5" class="mensagem-tabela">Nenhuma oferta disponível na última consulta.</td></tr>';
    return;
  }

  corpo.innerHTML = ofertas
    .map(
      (oferta) => `
        <tr>
          <td class="companhia">${escapar(oferta.companhia || "Não informada")}</td>
          <td>
            ${trecho(oferta.partida_ida, oferta.chegada_ida, oferta.duracao_ida)}
          </td>
          <td>
            ${trecho(oferta.partida_volta, oferta.chegada_volta, oferta.duracao_volta)}
          </td>
          <td class="conexoes">
            Ida: ${textoConexoes(oferta.conexoes_ida)}<br>
            Volta: ${textoConexoes(oferta.conexoes_volta)}
          </td>
          <td class="alinha-direita preco">${formatarPreco(oferta.preco_total)}</td>
        </tr>
      `,
    )
    .join("");
}

function trecho(partida, chegada, duracao) {
  return `
    <div class="trecho">
      <strong>${formatarVoo(partida)} → ${formatarVoo(chegada)}</strong>
      <small>${formatarDuracao(duracao)}</small>
    </div>
  `;
}

function desenharGrafico(historico) {
  const canvas = document.querySelector("#grafico-precos");
  const vazio = document.querySelector("#grafico-vazio");
  const consultas = historico.filter((item) => item.menor_preco != null);
  const pontos = agruparPrecosConsecutivos(consultas);
  document.querySelector("#quantidade-consultas").textContent =
    `${consultas.length} consulta${consultas.length === 1 ? "" : "s"} · ` +
    `${pontos.length} ponto${pontos.length === 1 ? "" : "s"}`;

  vazio.hidden = pontos.length > 0;
  canvas.hidden = pontos.length === 0;
  document.querySelector("#grafico-instrucao").hidden = pontos.length === 0;
  ocultarTooltipGrafico();
  coordenadasGrafico = [];
  if (!pontos.length) {
    return;
  }

  const proporcao = window.devicePixelRatio || 1;
  const largura = canvas.clientWidth;
  const altura = canvas.clientHeight;
  canvas.width = Math.floor(largura * proporcao);
  canvas.height = Math.floor(altura * proporcao);
  const contexto = canvas.getContext("2d");
  contexto.scale(proporcao, proporcao);

  const margem = { topo: 28, direita: 26, baixo: 38, esquerda: 72 };
  const larguraUtil = largura - margem.esquerda - margem.direita;
  const alturaUtil = altura - margem.topo - margem.baixo;
  const precos = pontos.map((ponto) => ponto.menor_preco);
  const minimo = Math.min(...precos);
  const maximo = Math.max(...precos);
  const intervalo = Math.max(maximo - minimo, Math.max(minimo * 0.08, 1));
  const limiteInferior = minimo - intervalo * 0.25;
  const limiteSuperior = maximo + intervalo * 0.25;

  contexto.font = "11px system-ui, sans-serif";
  contexto.textBaseline = "middle";
  contexto.lineWidth = 1;

  for (let indice = 0; indice <= 4; indice += 1) {
    const y = margem.topo + (alturaUtil / 4) * indice;
    const valor =
      limiteSuperior - ((limiteSuperior - limiteInferior) / 4) * indice;
    contexto.strokeStyle = "#e3e8e5";
    contexto.beginPath();
    contexto.moveTo(margem.esquerda, y);
    contexto.lineTo(largura - margem.direita, y);
    contexto.stroke();
    contexto.fillStyle = "#64706a";
    contexto.textAlign = "right";
    contexto.fillText(formatarPrecoCurto(valor), margem.esquerda - 10, y);
  }

  coordenadasGrafico = pontos.map((ponto, indice) => {
    const x =
      pontos.length === 1
        ? margem.esquerda + larguraUtil / 2
        : margem.esquerda + (larguraUtil / (pontos.length - 1)) * indice;
    const y =
      margem.topo +
      ((limiteSuperior - ponto.menor_preco) /
        (limiteSuperior - limiteInferior)) *
        alturaUtil;
    return { x, y, ponto };
  });

  contexto.strokeStyle = "#087852";
  contexto.lineWidth = 2.5;
  contexto.beginPath();
  coordenadasGrafico.forEach(({ x, y }, indice) => {
    if (indice === 0) {
      contexto.moveTo(x, y);
    } else {
      contexto.lineTo(x, y);
    }
  });
  contexto.stroke();

  coordenadasGrafico.forEach(({ x, y, ponto }, indice) => {
    contexto.fillStyle = ponto.queda_detectada ? "#f4bd3b" : "#087852";
    contexto.beginPath();
    contexto.arc(x, y, ponto.queda_detectada ? 5 : 4, 0, Math.PI * 2);
    contexto.fill();

    const mostrarData =
      pontos.length <= 6 ||
      indice === 0 ||
      indice === pontos.length - 1 ||
      indice % Math.ceil(pontos.length / 5) === 0;
    if (mostrarData) {
      contexto.fillStyle = "#64706a";
      contexto.textAlign = "center";
      contexto.textBaseline = "top";
      contexto.fillText(
        formatarDataCurta(ponto.consulta_em),
        x,
        altura - margem.baixo + 13,
      );
    }
  });
}

function agruparPrecosConsecutivos(consultas) {
  return consultas.reduce((grupos, consulta) => {
    const ultimoGrupo = grupos.at(-1);
    const precoEmCentavos = Math.round(Number(consulta.menor_preco) * 100);
    if (ultimoGrupo?.precoEmCentavos === precoEmCentavos) {
      ultimoGrupo.consulta_fim = consulta.consulta_em;
      ultimoGrupo.quantidade_consultas += 1;
      ultimoGrupo.queda_detectada ||= consulta.queda_detectada;
      return grupos;
    }

    grupos.push({
      ...consulta,
      consulta_inicio: consulta.consulta_em,
      consulta_fim: consulta.consulta_em,
      quantidade_consultas: 1,
      precoEmCentavos,
    });
    return grupos;
  }, []);
}

function configurarInteracaoGrafico() {
  const canvas = document.querySelector("#grafico-precos");
  const tratarInteracao = (evento) => {
    const retangulo = canvas.getBoundingClientRect();
    const x = evento.clientX - retangulo.left;
    const y = evento.clientY - retangulo.top;
    const pontoProximo = coordenadasGrafico
      .map((coordenada) => ({
        coordenada,
        distancia: Math.hypot(coordenada.x - x, coordenada.y - y),
      }))
      .sort((a, b) => a.distancia - b.distancia)[0];

    if (!pontoProximo || pontoProximo.distancia > 18) {
      ocultarTooltipGrafico();
      return;
    }
    exibirTooltipGrafico(pontoProximo.coordenada);
  };
  canvas.addEventListener("pointermove", tratarInteracao);
  canvas.addEventListener("pointerdown", tratarInteracao);
  canvas.addEventListener("pointerleave", ocultarTooltipGrafico);
}

function exibirTooltipGrafico({ x, y, ponto }) {
  const canvas = document.querySelector("#grafico-precos");
  const grafico = canvas.parentElement;
  const tooltip = document.querySelector("#grafico-tooltip");
  document.querySelector("#grafico-tooltip-preco").textContent =
    formatarPreco(ponto.menor_preco);
  document.querySelector("#grafico-tooltip-periodo").textContent =
    ponto.quantidade_consultas === 1
      ? `Consulta em ${formatarConsulta(ponto.consulta_inicio)}`
      : `${formatarConsulta(ponto.consulta_inicio)} → ${formatarConsulta(ponto.consulta_fim)}`;
  document.querySelector("#grafico-tooltip-quantidade").textContent =
    ponto.quantidade_consultas === 1
      ? "1 consulta"
      : `${ponto.quantidade_consultas} consultas agrupadas`;

  tooltip.hidden = false;
  const metadeTooltip = tooltip.offsetWidth / 2;
  const posicaoX = Math.min(
    grafico.clientWidth - metadeTooltip - 8,
    Math.max(metadeTooltip + 8, canvas.offsetLeft + x),
  );
  tooltip.style.left = `${posicaoX}px`;
  tooltip.style.top = `${canvas.offsetTop + y}px`;
  tooltip.classList.toggle("tooltip-abaixo", y < tooltip.offsetHeight + 18);
}

function ocultarTooltipGrafico() {
  document.querySelector("#grafico-tooltip").hidden = true;
}

function configurarLinkGitHub() {
  if (!window.location.hostname.endsWith("github.io")) {
    return;
  }
  const proprietario = window.location.hostname.split(".")[0];
  const repositorio = window.location.pathname.split("/").filter(Boolean)[0];
  if (!proprietario || !repositorio) {
    return;
  }
  const link = document.querySelector("#link-execucoes");
  link.href = `https://github.com/${proprietario}/${repositorio}/actions`;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.hidden = false;
}

function formatarPreco(valor) {
  return valor == null ? "—" : formatoMoeda.format(valor);
}

function formatarPrecoCurto(valor) {
  return `R$ ${Math.round(valor).toLocaleString("pt-BR")}`;
}

function formatarConsulta(valor) {
  return formatoConsulta.format(new Date(valor));
}

function formatarData(valor) {
  const [ano, mes, dia] = valor.split("-").map(Number);
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  })
    .format(new Date(ano, mes - 1, dia))
    .replace(".", "");
}

function formatarDataCurta(valor) {
  return formatoConsulta.format(new Date(valor)).split(",")[0];
}

function formatarVoo(valor) {
  if (!valor) {
    return "—";
  }
  const [data, hora] = valor.split("T");
  const [, mes, dia] = data.split("-");
  return `${dia}/${mes} ${hora.slice(0, 5)}`;
}

function formatarDuracao(valor) {
  const resultado = /^PT(?:(\d+)H)?(?:(\d+)M)?$/.exec(valor || "");
  if (!resultado) {
    return valor || "Duração não informada";
  }
  const horas = Number(resultado[1] || 0);
  const minutos = Number(resultado[2] || 0);
  return `${horas}h${String(minutos).padStart(2, "0")}`;
}

function textoConexoes(quantidade) {
  if (!quantidade) {
    return "direto";
  }
  return `${quantidade} conexão${quantidade === 1 ? "" : "ões"}`;
}

function escapar(valor) {
  return String(valor)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
