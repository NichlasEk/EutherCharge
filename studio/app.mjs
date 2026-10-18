import {
  BANKS,
  KNOWN_IMAGE_SIZE,
  KNOWN_SHA256,
  applyFixedTextPatch,
  digestHex,
  getPixel,
  hex,
  parseAllBanks,
  requiredBytes,
} from "./core.mjs";
import { SWEDISH } from "./sv-SE.mjs";

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const state = { source: null, working: null, sourceHash: null, banks: null, changes: new Map(), fileName: null };
const languageSelect = $("#languageSelect");
for (const bank of BANKS) languageSelect.add(new Option(`${bank.name}${bank.editable ? "" : " (endast läsning)"}`, bank.name));

let toastTimer;
function toast(message, error = false) {
  const node = $("#toast");
  node.textContent = message;
  node.classList.toggle("error", error);
  node.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => node.classList.remove("show"), 3300);
}

function setEnabled(enabled) {
  for (const selector of ["#languageSelect", "#stringFilter", "#applySwedish", "#resetEdits", "#exportImage", "#exportReport"]) {
    $(selector).disabled = !enabled;
  }
  for (const input of $$("#graphicsControls input, #graphicsControls select, #graphicsControls button")) input.disabled = !enabled;
}

async function loadFile(file) {
  try {
    const buffer = await file.arrayBuffer();
    const bytes = new Uint8Array(buffer);
    if (bytes.length !== KNOWN_IMAGE_SIZE) throw new Error(`Filen är ${bytes.length.toLocaleString("sv-SE")} byte, förväntat är 4 194 304.`);
    const banks = parseAllBanks(bytes);
    const hash = await digestHex(bytes);
    state.source = bytes;
    state.working = bytes.slice();
    state.sourceHash = hash;
    state.banks = banks;
    state.changes.clear();
    state.fileName = file.name;
    $("#fileStatus").textContent = file.name;
    $("#fileMeta").textContent = `${bytes.length.toLocaleString("sv-SE")} byte`;
    $("#hashStatus").textContent = hash === KNOWN_SHA256 ? "VERIFIERAD" : "OKÄND REVISION";
    $("#hashMeta").textContent = `${hash.slice(0, 16)}…`;
    $("#resourceStatus").textContent = `${banks.size} × 162`;
    $("#stringsEmpty").hidden = true;
    $("#stringList").hidden = false;
    setEnabled(true);
    renderStrings();
    renderRaw();
    updateChangeCount();
    toast(hash === KNOWN_SHA256 ? "Verifierad KW520 1.0.1-dump öppnad." : "Resurserna validerar, men filhashen avviker från referensen.", hash !== KNOWN_SHA256);
  } catch (error) {
    toast(`Kunde inte öppna: ${error.message}`, true);
  }
}

function updateChangeCount() {
  $("#changeCount").textContent = String(state.changes.size);
  $("#exportImage").disabled = !state.source || state.changes.size === 0;
}

function renderStrings() {
  if (!state.banks) return;
  const language = languageSelect.value;
  const filter = $("#stringFilter").value.trim().toLocaleLowerCase("sv");
  const entries = state.banks.get(language).filter((entry) => !filter || entry.text.toLocaleLowerCase("sv").includes(filter) || String(entry.index).includes(filter));
  const list = $("#stringList");
  list.replaceChildren();
  for (const entry of entries) {
    const key = `${entry.language}:${entry.index}`;
    const change = state.changes.get(key);
    const row = document.createElement("div");
    row.className = "string-row";
    const index = document.createElement("span");
    index.className = "string-index";
    index.textContent = `#${String(entry.index).padStart(3, "0")}`;
    index.title = `${hex(entry.recordOffset)} · pekare ${hex(entry.pointerOffset)}`;
    const original = document.createElement("span");
    original.className = "string-original";
    original.textContent = entry.text || "␀";
    const input = document.createElement("input");
    input.value = change?.afterText ?? entry.text;
    input.disabled = !entry.editable;
    input.setAttribute("aria-label", `${entry.language} post ${entry.index}`);
    const count = document.createElement("span");
    count.className = "string-bytes";
    const refreshCount = () => {
      const length = [...input.value].reduce((sum, char) => sum + (char.codePointAt(0) <= 0xff ? 1 : 999), 0);
      count.textContent = `${length}/${entry.capacity}`;
      input.classList.toggle("invalid", length > entry.capacity);
    };
    input.addEventListener("change", () => editString(entry, input));
    input.addEventListener("input", refreshCount);
    refreshCount();
    row.append(index, original, input, count);
    list.append(row);
  }
}

function rebuildWorking() {
  state.working = state.source.slice();
  for (const change of state.changes.values()) {
    const entry = state.banks.get(change.language)[change.index];
    applyFixedTextPatch(state.working, entry, change.afterText);
  }
}

function editString(entry, input) {
  const key = `${entry.language}:${entry.index}`;
  try {
    const test = state.source.slice();
    const change = applyFixedTextPatch(test, entry, input.value);
    if (input.value === entry.text) state.changes.delete(key);
    else state.changes.set(key, change);
    rebuildWorking();
    input.classList.remove("invalid");
    updateChangeCount();
    renderRaw();
  } catch (error) {
    input.classList.add("invalid");
    toast(error.message, true);
  }
}

function parseOffset(value) {
  const parsed = Number.parseInt(value.trim(), value.trim().toLowerCase().startsWith("0x") ? 16 : 10);
  if (!Number.isFinite(parsed) || parsed < 0) throw new Error("Ogiltigt offset");
  return parsed;
}

function renderRaw() {
  if (!state.working) return;
  try {
    const offset = parseOffset($("#rawOffset").value);
    const width = Number($("#rawWidth").value);
    const height = Number($("#rawHeight").value);
    const format = $("#rawFormat").value;
    const length = requiredBytes(width, height, format);
    if (offset + length > state.working.length) throw new Error("Pixelområdet går utanför dumpen");
    const canvas = $("#rawCanvas");
    canvas.width = width;
    canvas.height = height;
    const zoom = Number($("#rawZoom").value);
    canvas.style.width = `${width * zoom}px`;
    canvas.style.height = `${height * zoom}px`;
    const context = canvas.getContext("2d");
    const image = context.createImageData(width, height);
    for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
      image.data.set(getPixel(state.working, offset, width, height, format, x, y), (y * width + x) * 4);
    }
    context.putImageData(image, 0, 0);
    $("#canvasCaption").textContent = `${hex(offset)}–${hex(offset + length - 1)} · ${length} byte · ${format}`;
  } catch (error) {
    $("#canvasCaption").textContent = error.message;
  }
}

function stepRaw(direction) {
  const offset = parseOffset($("#rawOffset").value);
  const length = requiredBytes(Number($("#rawWidth").value), Number($("#rawHeight").value), $("#rawFormat").value);
  $("#rawOffset").value = hex(Math.max(0, offset + direction * length));
  renderRaw();
}

function download(data, filename, type) {
  const blob = new Blob([data], { type });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  link.click();
  setTimeout(() => URL.revokeObjectURL(link.href), 1000);
}

async function buildReport() {
  const outputHash = await digestHex(state.working);
  return {
    format: 1,
    tool: "EutherCharge Studio",
    operation: "kw520-fixed-allocation-text-patch",
    source: { file: state.fileName, size: state.source.length, sha256: state.sourceHash },
    output: { size: state.working.length, sha256: outputHash },
    referenceMatched: state.sourceHash === KNOWN_SHA256,
    invariants: {
      imageSizePreserved: state.source.length === state.working.length,
      pointerTablesModified: false,
      lengthPrefixesModified: false,
      scope: "verified language string payload bytes only",
    },
    changes: [...state.changes.values()],
  };
}

$("#fileInput").addEventListener("change", (event) => event.target.files[0] && loadFile(event.target.files[0]));
for (const eventName of ["dragenter", "dragover"]) $("#dropZone").addEventListener(eventName, (event) => { event.preventDefault(); $("#dropZone").classList.add("drag"); });
for (const eventName of ["dragleave", "drop"]) $("#dropZone").addEventListener(eventName, (event) => { event.preventDefault(); $("#dropZone").classList.remove("drag"); });
$("#dropZone").addEventListener("drop", (event) => event.dataTransfer.files[0] && loadFile(event.dataTransfer.files[0]));
languageSelect.addEventListener("change", renderStrings);
$("#stringFilter").addEventListener("input", renderStrings);
$("#applySwedish").addEventListener("click", () => {
  const entries = state.banks.get("English");
  const next = new Map(state.changes);
  try {
    entries.forEach((entry, index) => {
      const test = state.source.slice();
      const change = applyFixedTextPatch(test, entry, SWEDISH[index]);
      if (SWEDISH[index] !== entry.text) next.set(`English:${index}`, change);
    });
    state.changes = next;
    languageSelect.value = "English";
    rebuildWorking();
    renderStrings();
    renderRaw();
    updateChangeCount();
    toast("Svensk fastallokerad översättning tillagd i English-banken.");
  } catch (error) {
    toast(`Översättningen stoppades: ${error.message}`, true);
  }
});
$("#resetEdits").addEventListener("click", () => { state.changes.clear(); rebuildWorking(); renderStrings(); renderRaw(); updateChangeCount(); toast("Alla lokala patchar återställda."); });

for (const control of $$("#graphicsControls input, #graphicsControls select")) control.addEventListener("input", renderRaw);
for (const button of $$('[data-preset]')) button.addEventListener("click", () => {
  const rgb = button.dataset.preset === "rgb";
  $("#rawWidth").value = rgb ? 16 : 32;
  $("#rawHeight").value = rgb ? 16 : 32;
  $("#rawFormat").value = rgb ? "rgb565be" : "mono-row-msb";
  renderRaw();
});
for (const button of $$('[data-step]')) button.addEventListener("click", () => stepRaw(Number(button.dataset.step)));

for (const button of $$(".theme-button")) button.addEventListener("click", () => {
  $$(".theme-button").forEach((item) => item.classList.remove("active"));
  button.classList.add("active");
  $("#lcd").className = `lcd theme-${button.dataset.theme}`;
});
$("#eldrangButton").addEventListener("click", () => $("#lcd").classList.toggle("eldrang"));

const messages = ["Elektronerna har hittat arbetsmoralen.", "Motstånd är bara spänning med dålig attityd.", "Batteriet mediterar över 14,42 volt.", "Ampere in. Kaos under kontroll."];
let messageIndex = 0;
setInterval(() => { messageIndex = (messageIndex + 1) % messages.length; $("#chargeMessage").textContent = messages[messageIndex]; }, 4200);

let hymnTimer = null;
let hymnStep = 0;
$("#fanButton").addEventListener("click", () => {
  const bars = $$("#sequencer i");
  if (hymnTimer) {
    clearInterval(hymnTimer); hymnTimer = null; bars.forEach((bar) => bar.classList.remove("active")); $("#fanButton").textContent = "▶ STARTA"; return;
  }
  $("#fanButton").textContent = "■ AVBRYT";
  hymnTimer = setInterval(() => { bars.forEach((bar, index) => bar.classList.toggle("active", index === hymnStep || index === (hymnStep + 3) % 8)); hymnStep = (hymnStep + 1) % 8; }, 180);
});

$("#exportImage").addEventListener("click", async () => {
  const report = await buildReport();
  download(state.working, `euthercharge-kw520-${report.output.sha256.slice(0, 12)}.bin`, "application/octet-stream");
  toast("Modifierad image exporterad. Programmera den inte före separat bänkgranskning.");
});
$("#exportReport").addEventListener("click", async () => {
  const report = await buildReport();
  download(`${JSON.stringify(report, null, 2)}\n`, `euthercharge-report-${report.output.sha256.slice(0, 12)}.json`, "application/json");
});

setEnabled(false);
