from __future__ import annotations

import json
import os
import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from scripts.create_jppturismo_orcamento import generate_budget
from scripts.create_jppturismo_ordem import DEFAULT_DATA, generate


ROOT = Path(__file__).resolve().parent
ORDERS_DIR = ROOT / "output" / "pdf" / "ordens"
QUOTES_DIR = ROOT / "output" / "pdf" / "orcamentos"
ORDERS_DIR.mkdir(parents=True, exist_ok=True)
QUOTES_DIR.mkdir(parents=True, exist_ok=True)


PAGE = r"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>JPP Turismo - Ordem de Embarque</title>
  <link rel="manifest" href="/manifest.webmanifest">
  <meta name="theme-color" content="#0f3b5f">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <meta name="apple-mobile-web-app-title" content="JPP Turismo">
  <style>
    :root {
      --ink: #162433;
      --muted: #627083;
      --line: #d7dde5;
      --soft: #f5f7fa;
      --blue: #0f3b5f;
      --gold: #b98a32;
      --red: #c82d2d;
      --white: #ffffff;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: #eef2f6;
    }

    header {
      background: var(--white);
      border-bottom: 1px solid var(--line);
    }

    .bar {
      max-width: 1180px;
      margin: 0 auto;
      padding: 18px 22px;
      display: flex;
      justify-content: space-between;
      gap: 18px;
      align-items: center;
    }

    .brand {
      display: flex;
      align-items: baseline;
      gap: 12px;
      min-width: 220px;
    }

    .brand strong {
      font-size: 42px;
      line-height: 1;
      color: var(--blue);
      letter-spacing: 0;
    }

    .brand span {
      display: block;
      font-weight: 700;
      color: var(--gold);
      font-size: 18px;
    }

    .brand small {
      display: block;
      color: var(--blue);
      font-size: 12px;
      margin-top: 2px;
    }

    .company {
      text-align: right;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }

    main {
      max-width: 1180px;
      margin: 0 auto;
      padding: 22px;
    }

    .layout {
      display: grid;
      grid-template-columns: 1fr 320px;
      gap: 18px;
      align-items: start;
    }

    form {
      background: var(--white);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }

    .section {
      padding: 18px;
      border-bottom: 1px solid var(--line);
    }

    .section:last-child { border-bottom: 0; }

    h1, h2 {
      margin: 0;
      letter-spacing: 0;
    }

    h1 {
      font-size: 22px;
      line-height: 1.2;
    }

    h2 {
      font-size: 14px;
      text-transform: uppercase;
      color: var(--blue);
      margin-bottom: 14px;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
    }

    .span-2 { grid-column: span 2; }
    .span-3 { grid-column: span 3; }
    .span-4 { grid-column: span 4; }

    .tabs {
      display: flex;
      gap: 8px;
      padding: 0 18px 14px;
      background: var(--white);
      border-bottom: 1px solid var(--line);
      flex-wrap: wrap;
    }

    .tabs button {
      min-height: 36px;
      padding: 8px 12px;
      background: var(--white);
      color: var(--blue);
      border: 1px solid var(--line);
    }

    .tabs button.active {
      background: var(--blue);
      color: var(--white);
      border-color: var(--blue);
    }

    .tab-panel.hidden {
      display: none;
    }

    .manual-content.hidden {
      display: none;
    }

    label {
      display: grid;
      gap: 5px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }

    input, textarea {
      width: 100%;
      min-width: 0;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 10px 11px;
      font: inherit;
      color: var(--ink);
      background: var(--white);
    }

    textarea {
      min-height: 42px;
      resize: vertical;
    }

    .paste-area {
      min-height: 260px;
      line-height: 1.45;
    }

    .suggestions {
      display: grid;
      gap: 10px;
      margin-top: 14px;
    }

    .suggestion {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: var(--soft);
      display: grid;
      gap: 8px;
    }

    .suggestion strong {
      font-size: 14px;
      color: var(--ink);
    }

    .suggestion p {
      margin: 0;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }

    input:focus, textarea:focus {
      outline: 2px solid rgba(15, 59, 95, .18);
      border-color: var(--blue);
    }

    .actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 16px 18px;
      background: var(--soft);
      border-top: 1px solid var(--line);
    }

    button, .download {
      border: 0;
      border-radius: 6px;
      padding: 11px 16px;
      background: var(--blue);
      color: var(--white);
      font-weight: 700;
      cursor: pointer;
      text-decoration: none;
      font-size: 14px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 42px;
    }

    button.secondary {
      background: var(--white);
      color: var(--blue);
      border: 1px solid var(--line);
    }

    .status {
      min-height: 20px;
      color: var(--muted);
      font-size: 13px;
    }

    aside {
      background: var(--white);
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
    }

    .panel {
      padding: 16px;
      border-bottom: 1px solid var(--line);
    }

    .panel:last-child { border-bottom: 0; }

    .preview {
      aspect-ratio: 1 / 1.414;
      background: var(--soft);
      border: 1px solid var(--line);
      display: grid;
      align-content: start;
      gap: 8px;
      padding: 14px;
      font-size: 10px;
      color: #111;
    }

    .preview-logo {
      display: flex;
      justify-content: space-between;
      border-bottom: 2px solid #111;
      padding-bottom: 8px;
      margin-bottom: 4px;
    }

    .preview-logo b {
      font-size: 22px;
      color: var(--blue);
    }

    .preview-table {
      height: 18px;
      background: #c6c6c6;
      border: 1px solid #111;
      font-weight: 700;
      padding: 3px;
    }

    .history {
      display: grid;
      gap: 9px;
    }

    .history a {
      color: var(--blue);
      text-decoration: none;
      font-weight: 700;
      font-size: 13px;
      overflow-wrap: anywhere;
    }

    .share-button {
      background: var(--gold);
      color: var(--ink);
    }

    @media (max-width: 900px) {
      .layout { grid-template-columns: 1fr; }
      .grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .span-3, .span-4 { grid-column: span 2; }
      .company { text-align: left; }
      .bar { align-items: flex-start; flex-direction: column; }
    }

    @media (max-width: 560px) {
      main { padding: 12px; }
      .grid { grid-template-columns: 1fr; }
      .span-2, .span-3, .span-4 { grid-column: span 1; }
      .actions { align-items: stretch; flex-direction: column; }
      button, .download { width: 100%; }
    }
  </style>
</head>
<body>
  <header>
    <div class="bar">
      <div class="brand">
        <strong>JPP</strong>
        <div><span>TURISMO</span><small>executivo</small></div>
      </div>
      <div class="company">
        <div>CNPJ: 39.516.309/0001-74</div>
        <div>CADASTUR: 21.370015.44-6</div>
        <div>Canela - RS | (54) 98414-7613</div>
      </div>
    </div>
  </header>

  <main>
    <div class="layout">
      <form id="orderForm">
        <div class="section">
          <h1>Ordem de embarque</h1>
        </div>

        <div class="tabs">
          <button type="button" class="active" data-tab="manualPanel">Preencher</button>
          <button type="button" data-tab="pastePanel">Colar texto</button>
          <button type="button" data-tab="budgetPanel">Orcamento</button>
        </div>

        <div class="section tab-panel hidden" id="pastePanel">
          <h2>Colar texto</h2>
          <label>Mensagem ou orcamento
            <textarea class="paste-area" id="pasteText" placeholder="Cole aqui a conversa, roteiro ou orcamento recebido pelo WhatsApp."></textarea>
          </label>
          <div class="actions" style="margin:16px -18px -18px;">
            <div class="status" id="pasteStatus">Cole o texto e clique em ajustar dados.</div>
            <button type="button" id="parseBtn">Ajustar dados</button>
          </div>
          <div class="suggestions" id="suggestions"></div>
        </div>

        <div class="section tab-panel" id="manualPanel">
          <h2>Itinerario</h2>
          <div class="grid">
            <label>Numero<input name="itinerario" value="000001"></label>
            <label>Data<input name="data" value="29/06/2026 08:00"></label>
            <label>Retorno<input name="retorno" value="29/06/2026 12:00"></label>
            <label>Hora da tabela<input name="hora" value="08:00"></label>
            <label class="span-2">Veiculo<input name="veiculo" value="Van Executiva"></label>
            <label class="span-2">Operador<input name="operador" value="JPP Turismo Executivo"></label>
            <label class="span-2">Motorista<input name="motorista" value="A confirmar"></label>
            <label class="span-2">Guia<input name="guia"></label>
            <label class="span-4">Observacao<input name="observacao" value="Servico privativo"></label>
          </div>
        </div>

        <div class="section tab-panel hidden" id="budgetPanel">
          <h2>Orcamento para cliente</h2>
          <div class="grid">
            <label class="span-2">Cliente<input name="budget_cliente" value=""></label>
            <label class="span-2">Servico<input name="budget_servico" value=""></label>
            <label class="span-4">Periodo<input name="budget_periodo" value=""></label>
            <label class="span-4">Servicos incluidos<textarea name="budget_inclusos"></textarea></label>
            <label class="span-2">Passageiros<input name="budget_passageiros" value=""></label>
            <label>Valor total<input name="budget_total" value=""></label>
            <label>Valor por pessoa<input name="budget_por_pessoa" value=""></label>
            <label class="span-4">Observacoes<textarea name="budget_observacoes"></textarea></label>
          </div>
          <div class="actions" style="margin:16px -18px -18px;">
            <div class="status" id="budgetStatus">Puxe os dados da ordem ou preencha manualmente.</div>
            <div style="display:flex; gap:10px; flex-wrap:wrap;">
              <button class="secondary" type="button" id="copyOrderBtn">Puxar dados da ordem</button>
              <button type="button" id="budgetBtn">Gerar orcamento</button>
            </div>
          </div>
        </div>

        <div class="section manual-content">
          <h2>Servico e cliente</h2>
          <div class="grid">
            <label>Nro OS<input name="os" value="000000"></label>
            <label class="span-3">Cliente<input name="cliente" value="CLIENTE EXEMPLO"></label>
            <label class="span-2">Servico<input name="servico" value="Aeroporto / Hotel / Passeio"></label>
            <label class="span-2">Detalhe do servico<input name="servico_detalhe" value="Traslado privativo JPP Turismo"></label>
            <label class="span-2">Cliente - detalhe<input name="cliente_detalhe" value="CLIENTE EXEMPLO - ADT"></label>
            <label class="span-2">Destino / hotel<input name="destino" value="DESTINO / HOTEL"></label>
            <label class="span-2">Vendedor<input name="vendedor" value="JPP TURISMO"></label>
            <label class="span-2">Obs. venda<input name="obs_venda" value="Servico executivo"></label>
          </div>
        </div>

        <div class="section manual-content">
          <h2>Passageiros e cobranca</h2>
          <div class="grid">
            <label>ADT<input name="adt" type="number" min="0" value="1"></label>
            <label>CHD<input name="chd" type="number" min="0" value="0"></label>
            <label>INF<input name="inf" type="number" min="0" value="0"></label>
            <label>SEN<input name="sen" type="number" min="0" value="0"></label>
            <label>FREE<input name="free" type="number" min="0" value="0"></label>
            <label>Cobrar<input name="cobrar" value="--"></label>
          </div>
        </div>

        <div class="actions manual-content">
          <div class="status" id="status">Preencha os campos e gere o PDF.</div>
          <div style="display:flex; gap:10px; flex-wrap:wrap;">
            <button class="secondary" type="button" id="clearBtn">Limpar dados da viagem</button>
            <button type="submit">Gerar PDF</button>
          </div>
        </div>
      </form>

      <aside>
        <div class="panel">
          <h2>Previa</h2>
          <div class="preview">
            <div class="preview-logo"><b>JPP</b><span>ORDEM DE EMBARQUE<br>ITINERARIO</span></div>
            <strong id="pvClient">CLIENTE EXEMPLO</strong>
            <div id="pvService">Aeroporto / Hotel / Passeio</div>
            <div id="pvDate">29/06/2026 08:00</div>
            <div class="preview-table">Hor | Nro OS | Servico | Cliente</div>
            <div id="pvDest">&gt; DESTINO / HOTEL</div>
          </div>
        </div>
        <div class="panel">
          <h2>PDF gerado</h2>
          <div class="history" id="history">
            <span class="status">Nenhum PDF gerado nesta sessao.</span>
          </div>
        </div>
      </aside>
    </div>
  </main>

  <script>
    const form = document.getElementById("orderForm");
    const statusEl = document.getElementById("status");
    const historyEl = document.getElementById("history");
    const clearBtn = document.getElementById("clearBtn");
    const pasteText = document.getElementById("pasteText");
    const parseBtn = document.getElementById("parseBtn");
    const pasteStatus = document.getElementById("pasteStatus");
    const suggestionsEl = document.getElementById("suggestions");
    const tabButtons = document.querySelectorAll("[data-tab]");
    const copyOrderBtn = document.getElementById("copyOrderBtn");
    const budgetBtn = document.getElementById("budgetBtn");
    const budgetStatus = document.getElementById("budgetStatus");

    function values() {
      return Object.fromEntries(new FormData(form).entries());
    }

    function setValue(name, value) {
      const input = form.elements[name];
      if (input && value !== undefined && value !== null && value !== "") {
        input.value = value;
      }
    }

    function fillFields(data) {
      Object.entries(data).forEach(([key, value]) => setValue(key, value));
      copyOrderToBudget(false);
      Object.entries(data)
        .filter(([key]) => key.startsWith("budget_"))
        .forEach(([key, value]) => setValue(key, value));
      updatePreview();
    }

    function passengerText(data) {
      const parts = [];
      const labels = [["adt", "adulto"], ["chd", "crianca"], ["inf", "infantil"], ["sen", "senior"], ["free", "free"]];
      let total = 0;
      labels.forEach(([key, label]) => {
        const count = Number(data[key] || 0);
        if (count > 0) {
          total += count;
          parts.push(`${count} ${label}${count > 1 && label !== "free" ? "s" : ""}`);
        }
      });
      return parts.length ? `${total} pessoa${total === 1 ? "" : "s"} (${parts.join(", ")})` : "";
    }

    function copyOrderToBudget(showMessage = true) {
      const data = values();
      setValue("budget_cliente", data.cliente);
      setValue("budget_servico", data.servico);
      setValue("budget_periodo", [data.data ? `Chegada: ${data.data}` : "", data.retorno ? `Retorno: ${data.retorno}` : ""].filter(Boolean).join(" | "));
      setValue("budget_inclusos", data.servico_detalhe || data.servico);
      setValue("budget_passageiros", passengerText(data));
      setValue("budget_total", data.cobrar && data.cobrar !== "--" ? data.cobrar : "");
      setValue("budget_observacoes", data.obs_venda || data.observacao);
      if (showMessage) budgetStatus.textContent = "Dados da ordem puxados para o orcamento.";
    }

    function moneyNear(text, marker) {
      const index = text.toLowerCase().indexOf(marker.toLowerCase());
      if (index < 0) return "";
      const slice = text.slice(index, index + 500);
      const match = slice.match(/R\$\s*[\d.,]+/i);
      return match ? match[0].replace(/\s+/g, " ") : "";
    }

    function currentDateWith(time) {
      const current = form.elements.data.value || "";
      const date = (current.match(/\d{2}\/\d{2}\/\d{4}/) || [""])[0];
      return date ? `${date} ${time}` : time;
    }

    function firstTimeRange(text, fallbackEnd) {
      const range = text.match(/(?:das|de)\s*(\d{1,2}:\d{2})\s*(?:ate|até|as)\s*(\d{1,2}:\d{2})/i);
      if (range) return { start: range[1], end: range[2] };
      const start = text.match(/(\d{1,2}:\d{2})/);
      return { start: start ? start[1] : "09:00", end: fallbackEnd };
    }

    function monthNumber(name) {
      const months = {
        janeiro: "01", fevereiro: "02", marco: "03", março: "03", abril: "04",
        maio: "05", junho: "06", julho: "07", agosto: "08", setembro: "09",
        outubro: "10", novembro: "11", dezembro: "12"
      };
      return months[name.toLowerCase()] || "";
    }

    function dateByLabel(text, label) {
      const pattern = new RegExp(label + "\\s*:?\\s*(\\d{1,2})\\s+de\\s+([a-zç]+)\\s+de\\s+(\\d{4})\\s*\\((\\d{1,2}:\\d{2})\\)", "i");
      let match = text.match(pattern);
      if (!match) {
        match = text.match(new RegExp(label + "\\s*:?\\s*(\\d{1,2})\\s+de\\s+([a-zÃ§]+)\\s+de\\s+(\\d{4})", "i"));
      }
      if (!match) return "";
      const day = match[1].padStart(2, "0");
      const month = monthNumber(match[2]);
      return month ? `${day}/${month}/${match[3]}${match[4] ? " " + match[4] : ""}` : "";
    }

    function vehicleFromText(text) {
      const match = text.match(/ve[ií]culo indicado\s*:\s*([^\n\r]+)/i);
      return match ? match[1].trim() : "";
    }

    function simplifyFieldName(value) {
      return value
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .toLowerCase()
        .replace(/servi.o/g, "servico")
        .replace(/inclu.dos/g, "incluidos")
        .replace(/[^a-z0-9\s]/g, "")
        .replace(/\s+/g, " ")
        .trim();
    }

    function singleLineField(text, labels) {
      const wanted = labels.map(simplifyFieldName);
      const lines = text.split(/\n+/);
      for (const line of lines) {
        const separator = line.indexOf(":");
        if (separator < 0) continue;
        const fieldName = simplifyFieldName(line.slice(0, separator));
        if (wanted.includes(fieldName)) {
          return line.slice(separator + 1).trim();
        }
      }
      return "";
    }

    function blockField(text, labels) {
      const wanted = labels.map(simplifyFieldName);
      const lines = text.split(/\n+/);
      for (let i = 0; i < lines.length; i++) {
        const cleanLine = lines[i].trim();
        const fieldName = simplifyFieldName(cleanLine.replace(/:$/, ""));
        if (wanted.includes(fieldName)) {
          const block = [];
          for (let j = i + 1; j < lines.length; j++) {
            const next = lines[j].trim();
            if (!next) {
              if (block.length) break;
              continue;
            }
            const nextName = simplifyFieldName(next.split(":")[0] || next);
            if (/^(valor|observa|chegada|retorno|cliente|passageiros|servico)/i.test(nextName)) break;
            block.push(next);
          }
          return block.join(" | ");
        }
      }
      return "";
    }

    function clientFromText(text) {
      const named = text.match(/(?:nome do cliente|cliente)\s*:\s*([^\n\r]+)/i);
      if (named) return named[1].trim().toUpperCase();
      const line = text.split(/\n+/).map((item) => item.trim()).find((item) => /^(sr|sra|senhor|senhora|dona)\b/i.test(item));
      if (line) return line.replace(/\s+/g, " ").toUpperCase();
      return "";
    }

    function peopleFromText(text) {
      const match = text.match(/(\d+)\s*(?:pessoas|passageiros|adultos|clientes)/i);
      return match ? match[1] : "";
    }

    function passengerCounts(text) {
      const adults = text.match(/(\d+)\s*adultos?/i);
      const children = text.match(/(\d+)\s*crian[çc]as?/i);
      return {
        adt: adults ? adults[1] : peopleFromText(text) || "1",
        chd: children ? children[1] : "0"
      };
    }

    function detectSuggestions(text) {
      const normalized = text.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      const lower = normalized.toLowerCase();
      const client = clientFromText(text);
      const counts = passengerCounts(text);
      const arrival = dateByLabel(text, "Chegada");
      const departure = dateByLabel(text, "Retorno");
      const vehicle = vehicleFromText(text);
      const base = {
        cliente: client,
        cliente_detalhe: client ? `${client} - ADT` : "",
        data: arrival,
        retorno: departure,
        hora: (arrival.match(/\d{1,2}:\d{2}/) || [""])[0],
        adt: counts.adt,
        chd: counts.chd,
        inf: "0",
        sen: "0",
        free: "0",
        veiculo: vehicle || "Van Executiva",
        operador: "JPP Turismo Executivo",
        observacao: "Servico privativo",
        vendedor: "JPP TURISMO"
      };
      const suggestions = [];
      const explicitService = singleLineField(text, ["servico", "servicos"]);
      const explicitIncluded = blockField(text, ["servicos incluidos"]);
      const explicitTotal = singleLineField(text, ["Valor total", "Investimento total"]);
      const hasCompositeService = explicitService && (
        explicitService.toLowerCase().includes("transfer") &&
        (explicitService.toLowerCase().includes("city") || explicitService.toLowerCase().includes("+") || explicitService.toLowerCase().includes("tradicional"))
      );

      if (hasCompositeService || explicitIncluded) {
        const service = explicitService || explicitIncluded;
        const price = explicitTotal || moneyNear(text, "Valor total") || moneyNear(text, "Transfer");
        suggestions.push({
          title: service,
          description: `${explicitIncluded || service}${price ? " - " + price : ""}`,
          data: {
            ...base,
            servico: service,
            servico_detalhe: explicitIncluded || service,
            destino: "POA / Gramado / Canela / City Tour",
            obs_venda: price ? `${service} ${price}` : service,
            cobrar: price || "--",
            budget_servico: service,
            budget_inclusos: explicitIncluded || service,
            budget_total: price || "",
            budget_por_pessoa: singleLineField(text, ["Valor por pessoa"]),
            budget_observacoes: singleLineField(text, ["observacoes"])
          }
        });
        return suggestions;
      }

      if (lower.includes("transfer")) {
        const price = moneyNear(text, "Transfer");
        suggestions.push({
          title: "Transfer POA x Gramado",
          description: `Transfer privativo${price ? " - " + price : ""}`,
          data: {
            ...base,
            servico: "Transfer POA x Gramado",
            servico_detalhe: "Ida e volta - Porto Alegre x Gramado",
            destino: "POA x Gramado",
            obs_venda: price ? `Transfer ${price}` : "Transfer privativo ida e volta",
            cobrar: price || "--"
          }
        });
      }

      if (lower.includes("trem") || lower.includes("maria fumaca") || lower.includes("vinho")) {
        const price = moneyNear(text, "trem");
        suggestions.push({
          title: "Trem e vinho",
          description: `Bento Goncalves, Maria Fumaca e Epopeia Italiana${price ? " - " + price : ""}`,
          data: {
            ...base,
            servico: "Passeio trem e vinho",
            servico_detalhe: "Bento Goncalves + Maria Fumaca",
            destino: "Bento Goncalves / Vale dos Vinhedos",
            obs_venda: price ? `Trem e vinho ${price}` : "Passeio privativo",
            cobrar: price || "--"
          }
        });
      }

      if (lower.includes("premium")) {
        const hours = firstTimeRange(text.slice(lower.indexOf("premium")), "22:30");
        suggestions.push({
          title: "Passeio premium",
          description: `Passeio privativo das ${hours.start} ate ${hours.end}`,
          data: {
            ...base,
            hora: hours.start,
            data: currentDateWith(hours.start),
            retorno: currentDateWith(hours.end),
            servico: "Passeio pacote premium",
            servico_detalhe: "Carro a disposicao do cliente",
            destino: "Serra Gaucha",
            obs_venda: `Das ${hours.start} ate ${hours.end}`,
          }
        });
      }

      if (lower.includes("tradicional")) {
        const hours = firstTimeRange(text.slice(lower.indexOf("tradicional")), "17:30");
        suggestions.push({
          title: "Passeio tradicional",
          description: `Passeio privativo das ${hours.start} ate ${hours.end}`,
          data: {
            ...base,
            hora: hours.start,
            data: currentDateWith(hours.start),
            retorno: currentDateWith(hours.end),
            servico: "Passeio pacote tradicional",
            servico_detalhe: "Carro a disposicao do cliente",
            destino: "Serra Gaucha",
            obs_venda: `Das ${hours.start} ate ${hours.end}`,
          }
        });
      }

      if (!suggestions.length) {
        suggestions.push({
          title: "Dados encontrados",
          description: "Preenchimento basico a partir do texto colado.",
          data: base
        });
      }

      return suggestions;
    }

    function renderSuggestions(suggestions) {
      suggestionsEl.innerHTML = "";
      suggestions.forEach((item) => {
        const card = document.createElement("div");
        card.className = "suggestion";
        card.innerHTML = `<strong>${item.title}</strong><p>${item.description}</p>`;
        const button = document.createElement("button");
        button.type = "button";
        button.textContent = "Usar estes dados";
        button.addEventListener("click", () => {
          fillFields(item.data);
          pasteStatus.textContent = `Dados aplicados: ${item.title}.`;
          statusEl.textContent = "Confira os campos e gere o PDF.";
          showTab("manualPanel");
        });
        card.appendChild(button);
        suggestionsEl.appendChild(card);
      });
    }

    function showTab(id) {
      document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.toggle("hidden", panel.id !== id));
      document.querySelectorAll(".manual-content").forEach((panel) => panel.classList.toggle("hidden", id !== "manualPanel"));
      tabButtons.forEach((button) => button.classList.toggle("active", button.dataset.tab === id));
    }

    function updatePreview() {
      const data = values();
      document.getElementById("pvClient").textContent = data.cliente || "CLIENTE";
      document.getElementById("pvService").textContent = data.servico || "Servico";
      document.getElementById("pvDate").textContent = data.data || "Data";
      document.getElementById("pvDest").textContent = "> " + (data.destino || "Destino");
    }

    async function sharePdf(result) {
      const absoluteUrl = new URL(result.url, window.location.href).href;
      try {
        const response = await fetch(result.url);
        const blob = await response.blob();
        const file = new File([blob], result.name, { type: "application/pdf" });
        if (navigator.canShare && navigator.canShare({ files: [file] })) {
          await navigator.share({ title: result.name, text: "PDF JPP Turismo", files: [file] });
          return;
        }
        if (navigator.share) {
          await navigator.share({ title: result.name, text: "PDF JPP Turismo", url: absoluteUrl });
          return;
        }
      } catch (error) {
      }
      await navigator.clipboard.writeText(absoluteUrl);
      alert("Link do PDF copiado.");
    }

    function showGeneratedPdf(result) {
      historyEl.innerHTML = "";
      const link = document.createElement("a");
      link.className = "download";
      link.href = result.url;
      link.target = "_blank";
      link.textContent = result.name;
      historyEl.appendChild(link);

      const share = document.createElement("button");
      share.type = "button";
      share.className = "share-button";
      share.textContent = "Compartilhar PDF";
      share.addEventListener("click", () => sharePdf(result));
      historyEl.appendChild(share);
    }

    form.addEventListener("input", updatePreview);

    copyOrderBtn.addEventListener("click", () => copyOrderToBudget(true));

    budgetBtn.addEventListener("click", async () => {
      budgetStatus.textContent = "Gerando orcamento...";
      const response = await fetch("/api/generate-budget", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values())
      });
      if (!response.ok) {
        budgetStatus.textContent = "Nao foi possivel gerar o orcamento.";
        return;
      }
      const result = await response.json();
      budgetStatus.textContent = "Orcamento gerado com sucesso.";
      showGeneratedPdf(result);
    });

    tabButtons.forEach((button) => {
      button.addEventListener("click", () => showTab(button.dataset.tab));
    });

    parseBtn.addEventListener("click", () => {
      const text = pasteText.value.trim();
      if (!text) {
        pasteStatus.textContent = "Cole um texto antes de ajustar.";
        suggestionsEl.innerHTML = "";
        return;
      }
      const suggestions = detectSuggestions(text);
      renderSuggestions(suggestions);
      pasteStatus.textContent = `${suggestions.length} sugestao(oes) encontrada(s).`;
      if (suggestions.length === 1) {
        fillFields(suggestions[0].data);
      }
    });

    clearBtn.addEventListener("click", () => {
      ["itinerario", "data", "retorno", "hora", "os", "cliente", "servico", "servico_detalhe", "cliente_detalhe", "destino"].forEach((name) => {
        const input = form.elements[name];
        if (input) input.value = "";
      });
      updatePreview();
      statusEl.textContent = "Campos da viagem limpos.";
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      statusEl.textContent = "Gerando PDF...";

      const response = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values())
      });

      if (!response.ok) {
        statusEl.textContent = "Nao foi possivel gerar o PDF.";
        return;
      }

      const result = await response.json();
      statusEl.textContent = "PDF gerado com sucesso.";
      showGeneratedPdf(result);
    });

    updatePreview();

    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("/service-worker.js").catch(() => {});
    }
  </script>
</body>
</html>
"""


MANIFEST = {
    "name": "JPP Turismo",
    "short_name": "JPP Turismo",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#eef2f6",
    "theme_color": "#0f3b5f",
    "icons": [
        {
            "src": "/icon.svg",
            "sizes": "any",
            "type": "image/svg+xml",
            "purpose": "any maskable",
        }
    ],
}


SERVICE_WORKER = """const CACHE = "jpp-turismo-v1";
self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE).then((cache) => cache.addAll(["/", "/manifest.webmanifest", "/icon.svg"])));
});
self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
"""


ICON_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <rect width="512" height="512" rx="96" fill="#0f3b5f"/>
  <text x="72" y="250" fill="#fff" font-family="Arial, Helvetica, sans-serif" font-size="128" font-weight="700">JPP</text>
  <text x="78" y="330" fill="#d6ae5a" font-family="Arial, Helvetica, sans-serif" font-size="54" font-weight="700">TURISMO</text>
</svg>
"""


def slug(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "ordem"


def pdf_name(data: dict) -> str:
    itinerary = slug(str(data.get("itinerario", "ordem")))
    client = slug(str(data.get("cliente", "cliente")))[:32]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"jpp-ordem-{itinerary}-{client}-{stamp}.pdf"


def budget_name(data: dict) -> str:
    client = slug(str(data.get("budget_cliente") or data.get("cliente") or "cliente"))[:32]
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"jpp-orcamento-{client}-{stamp}.pdf"


class AppHandler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:
        return

    def send_bytes(self, body: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = unquote(self.path.split("?", 1)[0])
        if path == "/":
            self.send_bytes(PAGE.encode("utf-8"), "text/html; charset=utf-8")
            return

        if path == "/manifest.webmanifest":
            self.send_bytes(json.dumps(MANIFEST).encode("utf-8"), "application/manifest+json; charset=utf-8")
            return

        if path == "/service-worker.js":
            self.send_bytes(SERVICE_WORKER.encode("utf-8"), "application/javascript; charset=utf-8")
            return

        if path == "/icon.svg":
            self.send_bytes(ICON_SVG.encode("utf-8"), "image/svg+xml; charset=utf-8")
            return

        if path.startswith("/pdf/"):
            target = (ORDERS_DIR / path.removeprefix("/pdf/")).resolve()
            if ORDERS_DIR.resolve() in target.parents and target.exists():
                self.send_bytes(target.read_bytes(), "application/pdf")
                return

        if path.startswith("/orcamento/"):
            target = (QUOTES_DIR / path.removeprefix("/orcamento/")).resolve()
            if QUOTES_DIR.resolve() in target.parents and target.exists():
                self.send_bytes(target.read_bytes(), "application/pdf")
                return

        self.send_bytes(b"Not found", "text/plain; charset=utf-8", 404)

    def do_POST(self) -> None:
        if self.path not in ["/api/generate", "/api/generate-budget"]:
            self.send_bytes(b"Not found", "text/plain; charset=utf-8", 404)
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError:
            self.send_bytes(b"Invalid JSON", "text/plain; charset=utf-8", 400)
            return

        if self.path == "/api/generate-budget":
            filename = budget_name(data)
            out_file = QUOTES_DIR / filename
            generate_budget(data, out_file)
            body = json.dumps({"name": filename, "url": f"/orcamento/{filename}"}).encode("utf-8")
            self.send_bytes(body, "application/json; charset=utf-8")
            return

        filename = pdf_name(data)
        out_file = ORDERS_DIR / filename
        generate(data, out_file)
        body = json.dumps({"name": filename, "url": f"/pdf/{filename}"}).encode("utf-8")
        self.send_bytes(body, "application/json; charset=utf-8")


def run(host: str = "127.0.0.1", port: int = 8765) -> None:
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run(os.environ.get("HOST", "127.0.0.1"), int(os.environ.get("PORT", "8765")))
