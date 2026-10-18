#!/usr/bin/env node
/** Build a Swedish fixed-allocation KW520 image from the verified reference. */

import fs from "node:fs";
import path from "node:path";
import {
  BANKS,
  KNOWN_IMAGE_SIZE,
  KNOWN_SHA256,
  applyFixedTextPatch,
  digestHex,
  parseAllBanks,
} from "../studio/core.mjs";
import { SWEDISH } from "../studio/sv-SE.mjs";

function usage() {
  console.error("Usage: node tools/build-swedish.mjs INPUT.bin OUTPUT.bin");
  process.exit(2);
}

const [, , inputName, outputName] = process.argv;
if (!inputName || !outputName || process.argv.length !== 4) usage();

const input = path.resolve(inputName);
const output = path.resolve(outputName);
if (input === output) throw new Error("Vägrar skriva över källfilen");
if (fs.existsSync(output)) throw new Error(`Målfilen finns redan: ${output}`);

const sourceBuffer = fs.readFileSync(input);
const source = new Uint8Array(sourceBuffer);
if (source.length !== KNOWN_IMAGE_SIZE) throw new Error(`Fel storlek: ${source.length} byte`);
const sourceHash = await digestHex(source);
if (sourceHash !== KNOWN_SHA256) {
  throw new Error(`Källhashen är inte den verifierade KW520 1.0.1-referensen: ${sourceHash}`);
}

const banks = parseAllBanks(source);
const english = banks.get(BANKS[0].name);
const modified = source.slice();
const changes = english
  .map((entry, index) => applyFixedTextPatch(modified, entry, SWEDISH[index]))
  .filter((change) => change.beforeHex !== change.afterHex);
const reparsed = parseAllBanks(modified).get("English");
if (!reparsed.every((entry, index) => entry.text === SWEDISH[index])) {
  throw new Error("Intern kontroll misslyckades: exporterad svensk bank kunde inte läsas tillbaka");
}
const allowed = new Uint8Array(source.length);
for (const entry of english) {
  allowed.fill(1, entry.payloadOffset, entry.payloadOffset + entry.allocation);
}
let changedByteCount = 0;
for (let offset = 0; offset < source.length; offset += 1) {
  if (source[offset] === modified[offset]) continue;
  changedByteCount += 1;
  if (!allowed[offset]) throw new Error(`Otillåten ändring utanför English-payload vid 0x${offset.toString(16)}`);
}
const outputHash = await digestHex(modified);
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, modified);

const report = {
  format: 1,
  tool: "tools/build-swedish.mjs",
  operation: "kw520-fixed-allocation-swedish-translation",
  source: { path: inputName, size: source.length, sha256: sourceHash },
  output: { path: outputName, size: modified.length, sha256: outputHash },
  changedByteCount,
  invariants: {
    knownReferenceRequired: true,
    imageSizePreserved: source.length === modified.length,
    pointerTablesModified: false,
    lengthPrefixesModified: false,
    bank: "English",
    scope: "162 verified string payload allocations only",
  },
  changes,
};
fs.writeFileSync(`${output}.manifest.json`, `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log(`Wrote ${outputName}`);
console.log(`SHA-256: ${outputHash}`);
console.log(`Manifest: ${outputName}.manifest.json`);
