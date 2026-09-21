/**
 * Marin arealplanlægning – Limfjorden ved Aalborg (testudkast)
 *
 * Indlæser kriterie-konfiguration + GIS-polygoner (GeoJSON, dummy-data),
 * tegner dem på et Leaflet-kort og lader brugeren vægte kriterierne mod
 * hinanden via skydere. Den samlede egnethedsscore genberegnes og kortet
 * omfarves live, uden at hente data igen.
 */

const DATA_DIR = "data";
const SEQ_RAMP = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"];
const NO_WEIGHT_FILL = "#e1e0d9";
const ACCENT_DOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#008300"];

const state = {
  config: null,
  weights: {}, // felt -> 0..100
  gridLayer: null,
};

init();

async function init() {
  const [config, grid, studyArea] = await Promise.all([
    fetchJSON(`${DATA_DIR}/kriterier_config.json`),
    fetchJSON(`${DATA_DIR}/kriterier_grid.geojson`),
    fetchJSON(`${DATA_DIR}/studieomraade.geojson`),
  ]);

  state.config = config;
  config.kriterier.forEach((k) => {
    state.weights[k.felt] = k.standardvaegt;
  });

  applyTextContent(config);
  buildSliders(config);
  buildLegend();

  const map = buildMap(studyArea);
  state.gridLayer = buildGridLayer(grid, map);

  document.getElementById("reset-btn").addEventListener("click", () => {
    config.kriterier.forEach((k) => {
      state.weights[k.felt] = k.standardvaegt;
    });
    document.querySelectorAll("#sliders input[type=range]").forEach((input) => {
      input.value = state.weights[input.dataset.felt];
      input.nextElementSibling && updateSliderValueLabel(input);
    });
    document.querySelectorAll(".slider-value").forEach((el) => {
      el.textContent = `${state.weights[el.dataset.felt]}`;
    });
    state.gridLayer.setStyle(styleForFeature);
    hideDetail();
  });
}

async function fetchJSON(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Kunne ikke hente ${path}: ${res.status}`);
  return res.json();
}

function applyTextContent(config) {
  document.title = config.titel || document.title;
  const titleEl = document.getElementById("site-title");
  const subtitleEl = document.getElementById("site-subtitle");
  if (config.titel) titleEl.textContent = config.titel.split("–")[0].trim();
  if (config.undertitel) subtitleEl.textContent = config.undertitel;
}

// ---------------------------------------------------------------------------
// Sidebar: skydere
// ---------------------------------------------------------------------------

function buildSliders(config) {
  const container = document.getElementById("sliders");
  container.innerHTML = "";

  config.kriterier.forEach((k, i) => {
    const row = document.createElement("div");
    row.className = "slider-row";

    const top = document.createElement("div");
    top.className = "row-top";

    const label = document.createElement("span");
    label.className = "slider-label";
    const dot = document.createElement("span");
    dot.className = "dot";
    dot.style.background = ACCENT_DOTS[i % ACCENT_DOTS.length];
    label.appendChild(dot);
    label.appendChild(document.createTextNode(k.navn));

    const valueEl = document.createElement("span");
    valueEl.className = "slider-value";
    valueEl.dataset.felt = k.felt;
    valueEl.textContent = `${k.standardvaegt}`;

    top.appendChild(label);
    top.appendChild(valueEl);

    const desc = document.createElement("p");
    desc.className = "slider-desc";
    desc.textContent = k.beskrivelse || "";

    const input = document.createElement("input");
    input.type = "range";
    input.min = "0";
    input.max = "100";
    input.step = "1";
    input.value = String(k.standardvaegt);
    input.dataset.felt = k.felt;
    input.setAttribute("aria-label", `Vægt for ${k.navn}`);

    input.addEventListener("input", () => {
      state.weights[k.felt] = Number(input.value);
      valueEl.textContent = input.value;
      if (state.gridLayer) state.gridLayer.setStyle(styleForFeature);
      refreshDetailIfOpen();
    });

    row.appendChild(top);
    row.appendChild(desc);
    row.appendChild(input);
    container.appendChild(row);
  });
}

function updateSliderValueLabel(input) {
  const label = input.parentElement.querySelector(".slider-value");
  if (label) label.textContent = input.value;
}

function buildLegend() {
  const grad = document.getElementById("legend-gradient");
  grad.style.background = `linear-gradient(90deg, ${SEQ_RAMP.join(", ")})`;
}

// ---------------------------------------------------------------------------
// Score-beregning
// ---------------------------------------------------------------------------

function computeScore(props) {
  let weightSum = 0;
  let scoreSum = 0;
  for (const [felt, w] of Object.entries(state.weights)) {
    if (w <= 0) continue;
    const v = props[felt];
    if (typeof v !== "number") continue;
    weightSum += w;
    scoreSum += w * v;
  }
  if (weightSum === 0) return null;
  return scoreSum / weightSum;
}

function colorForScore(score) {
  if (score === null) return NO_WEIGHT_FILL;
  const idx = Math.min(SEQ_RAMP.length - 1, Math.floor((score / 100) * SEQ_RAMP.length));
  return SEQ_RAMP[Math.max(0, idx)];
}

function styleForFeature(feature) {
  const score = computeScore(feature.properties);
  return {
    fillColor: colorForScore(score),
    fillOpacity: 0.8,
    color: "#fcfcfb",
    weight: 1,
    opacity: 1,
  };
}

// ---------------------------------------------------------------------------
// Kort
// ---------------------------------------------------------------------------

function buildMap(studyAreaGeoJSON) {
  const map = L.map("map", { zoomControl: true, minZoom: 9 });

  // Esri "World Light Gray" canvas - minimal, key-free basemap (base + reference/label overlay)
  L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}",
    {
      attribution: "Kortgrundlag &copy; Esri",
      maxZoom: 16,
    }
  ).addTo(map);
  L.tileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}",
    { maxZoom: 16 }
  ).addTo(map);

  const studyLayer = L.geoJSON(studyAreaGeoJSON, {
    style: {
      color: "#184f95",
      weight: 2,
      dashArray: "6 4",
      fill: false,
    },
    interactive: false,
  }).addTo(map);

  map.fitBounds(studyLayer.getBounds(), { padding: [16, 16] });
  return map;
}

function buildGridLayer(geojson, map) {
  let activeLayer = null;

  const layer = L.geoJSON(geojson, {
    style: styleForFeature,
    onEachFeature: (feature, lyr) => {
      lyr.bindTooltip(() => tooltipHTML(feature.properties), {
        className: "cell-tooltip",
        sticky: true,
      });

      lyr.on("mouseover", () => {
        lyr.setStyle({ weight: 2, color: "#0b0b0b" });
        lyr.bringToFront();
      });
      lyr.on("mouseout", () => {
        if (lyr !== activeLayer) layer.resetStyle(lyr);
      });
      lyr.on("click", () => {
        if (activeLayer && activeLayer !== lyr) layer.resetStyle(activeLayer);
        activeLayer = lyr;
        lyr.setStyle({ weight: 3, color: "#0b0b0b" });
        showDetail(feature.properties);
      });
    },
  }).addTo(map);

  return layer;
}

function tooltipHTML(props) {
  const score = computeScore(props);
  const scoreText = score === null ? "–" : score.toFixed(0);
  return `<strong>Celle ${props.cell_id}</strong><br>Egnethedsscore: ${scoreText}`;
}

// ---------------------------------------------------------------------------
// Detaljepanel
// ---------------------------------------------------------------------------

let lastSelectedProps = null;

function showDetail(props) {
  lastSelectedProps = props;
  const panel = document.getElementById("detail-panel");
  const body = document.getElementById("detail-body");
  document.getElementById("detail-id").textContent = `#${props.cell_id}`;

  const score = computeScore(props);
  const rows = state.config.kriterier
    .map((k, i) => {
      const v = props[k.felt];
      const w = state.weights[k.felt];
      return `<div class="detail-row">
        <span class="name"><span class="dot" style="width:8px;height:8px;background:${ACCENT_DOTS[i % ACCENT_DOTS.length]}"></span>${k.navn}</span>
        <span class="value">${typeof v === "number" ? v.toFixed(1) : "–"} <span class="muted">(vægt ${w})</span></span>
      </div>`;
    })
    .join("");

  body.innerHTML = `
    ${rows}
    <div class="detail-total">
      <span>Vægtet score</span>
      <span class="value">${score === null ? "–" : score.toFixed(1)}</span>
    </div>
  `;
  panel.hidden = false;
}

function refreshDetailIfOpen() {
  if (lastSelectedProps) showDetail(lastSelectedProps);
}

function hideDetail() {
  lastSelectedProps = null;
  document.getElementById("detail-panel").hidden = true;
}
