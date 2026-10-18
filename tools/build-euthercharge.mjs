#!/usr/bin/env node
/** Build the integrated Swedish + EUTHERCHARGE-logo KW520 image. */

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
import {
  LOGO_HEIGHT,
  LOGO_OFFSET,
  LOGO_SIZE,
  LOGO_WIDTH,
  decodeColumnLsb,
  encodeColumnLsb,
  generateEutherChargeLogo,
} from "../studio/boot-logo.mjs";
import { SWEDISH } from "../studio/sv-SE.mjs";

function usage() {
  console.error("Usage: node tools/build-euthercharge.mjs INPUT.bin OUTPUT.bin");
  process.exit(2);
}

const [, , inputName, outputName] = process.argv;
if (!inputName || !outputName || process.argv.length !== 4) usage();
const input = path.resolve(inputName);
const output = path.resolve(outputName);
if (input === output) throw new Error("Vägrar skriva över källfilen");
if (fs.existsSync(output)) throw new Error(`Målfilen finns redan: ${output}`);

const source = new Uint8Array(fs.readFileSync(input));
if (source.length !== KNOWN_IMAGE_SIZE) throw new Error(`Fel storlek: ${source.length} byte`);
const sourceHash = await digestHex(source);
if (sourceHash !== KNOWN_SHA256) throw new Error(`Källhashen är inte verifierad KW520 1.0.1: ${sourceHash}`);

const banks = parseAllBanks(source);
const english = banks.get(BANKS[0].name);
const modified = source.slice();
const textChanges = english
  .map((entry, index) => applyFixedTextPatch(modified, entry, SWEDISH[index]))
  .filter((change) => change.beforeHex !== change.afterHex);

const oldLogo = source.slice(LOGO_OFFSET, LOGO_OFFSET + LOGO_SIZE);
const newLogoPixels = generateEutherChargeLogo();
const newLogo = encodeColumnLsb(newLogoPixels);
if (newLogo.length !== LOGO_SIZE) throw new Error(`Intern logotypstorlek är ${newLogo.length}, väntat ${LOGO_SIZE}`);
modified.set(newLogo, LOGO_OFFSET);

const reparsed = parseAllBanks(modified).get("English");
if (!reparsed.every((entry, index) => entry.text === SWEDISH[index])) {
  throw new Error("Återläsning av svensk bank misslyckades");
}
const decodedLogo = decodeColumnLsb(modified);
if (!decodedLogo.every((pixel, index) => pixel === newLogoPixels[index])) {
  throw new Error("Återläsning av EUTHERCHARGE-logga misslyckades");
}

const allowed = new Uint8Array(source.length);
allowed.fill(1, LOGO_OFFSET, LOGO_OFFSET + LOGO_SIZE);
for (const entry of english) allowed.fill(1, entry.payloadOffset, entry.payloadOffset + entry.allocation);
let changedByteCount = 0;
for (let offset = 0; offset < source.length; offset += 1) {
  if (source[offset] === modified[offset]) continue;
  changedByteCount += 1;
  if (!allowed[offset]) throw new Error(`Otillåten ändring vid 0x${offset.toString(16)}`);
}

const outputHash = await digestHex(modified);
fs.mkdirSync(path.dirname(output), { recursive: true });
fs.writeFileSync(output, modified);
const report = {
  format: 1,
  tool: "tools/build-euthercharge.mjs",
  operation: "kw520-integrated-swedish-and-logo-patch",
  source: { path: inputName, size: source.length, sha256: sourceHash },
  output: { path: outputName, size: modified.length, sha256: outputHash },
  changedByteCount,
  invariants: {
    knownReferenceRequired: true,
    imageSizePreserved: source.length === modified.length,
    pointerTablesModified: false,
    lengthPrefixesModified: false,
    modifiedAreas: ["128x32 logo resource 0x000000-0x0001ff (runtime use unconfirmed)", "English string payload allocations"],
  },
  graphics: [{
    name: "EUTHERCHARGE logo resource (runtime use unconfirmed)",
    offset: LOGO_OFFSET,
    length: LOGO_SIZE,
    width: LOGO_WIDTH,
    height: LOGO_HEIGHT,
    format: "1bpp-column-major-lsb-first",
    sourceSha256: await digestHex(oldLogo),
    replacementSha256: await digestHex(newLogo),
  }],
  textChanges,
};
fs.writeFileSync(`${output}.manifest.json`, `${JSON.stringify(report, null, 2)}\n`, "utf8");
console.log(`Wrote ${outputName}`);
console.log(`SHA-256: ${outputHash}`);
console.log(`Changed bytes: ${changedByteCount}`);
console.log(`Manifest: ${outputName}.manifest.json`);
