import test from "node:test";
import assert from "node:assert/strict";
import {
  POINTER_BASE,
  ENTRY_COUNT,
  parseBank,
  applyFixedTextPatch,
  getPixel,
  requiredBytes,
} from "../studio/core.mjs";
import { SWEDISH } from "../studio/sv-SE.mjs";

function fixture() {
  const bank = { name: "Test", tableOffset: 0x1000, stringsOffset: 0x3400, editable: true };
  const data = new Uint8Array(0x8000).fill(0xff);
  const view = new DataView(data.buffer);
  let cursor = bank.stringsOffset;
  for (let index = 0; index < ENTRY_COUNT; index += 1) {
    view.setUint32(bank.tableOffset + index * 4, cursor - POINTER_BASE, false);
    const payload = new TextEncoder().encode(`E${index}\0`);
    view.setUint16(cursor, payload.length, false);
    data.set(payload, cursor + 2);
    cursor += 2 + payload.length;
  }
  return { data, bank };
}

test("parses all fixed string records", () => {
  const { data, bank } = fixture();
  const entries = parseBank(data, bank);
  assert.equal(entries.length, 162);
  assert.equal(entries[0].text, "E0");
  assert.equal(entries[161].text, "E161");
});

test("fixed patch leaves prefix and file size unchanged", () => {
  const { data, bank } = fixture();
  const entry = parseBank(data, bank)[100];
  const prefix = data.slice(entry.recordOffset, entry.recordOffset + 2);
  const size = data.length;
  applyFixedTextPatch(data, entry, "X");
  assert.equal(data.length, size);
  assert.deepEqual(data.slice(entry.recordOffset, entry.recordOffset + 2), prefix);
  assert.deepEqual(data.slice(entry.payloadOffset, entry.payloadOffset + 5), Uint8Array.of(88, 0, 0, 0, 0));
});

test("fixed patch rejects overflow", () => {
  const { data, bank } = fixture();
  const entry = parseBank(data, bank)[0];
  assert.throws(() => applyFixedTextPatch(data, entry, "TOO-LONG"), /ryms inte/);
});

test("raw decoder supports row and RGB565 hypotheses", () => {
  assert.deepEqual(getPixel(Uint8Array.of(0x80), 0, 8, 1, "mono-row-msb", 0, 0), [255, 151, 27, 255]);
  assert.deepEqual(getPixel(Uint8Array.of(0xf8, 0x00), 0, 1, 1, "rgb565be", 0, 0), [255, 0, 0, 255]);
  assert.equal(requiredBytes(16, 16, "rgb565be"), 512);
  assert.deepEqual(getPixel(Uint8Array.of(0xf0), 0, 2, 1, "indexed4-high", 0, 0), [255, 255, 255, 255]);
  assert.deepEqual(getPixel(Uint8Array.of(0xc0), 0, 4, 1, "indexed2-msb", 0, 0), [255, 255, 255, 255]);
  assert.equal(requiredBytes(16, 16, "indexed4-high"), 128);
});

test("Swedish starter has exactly one Latin-1 string per entry", () => {
  assert.equal(SWEDISH.length, ENTRY_COUNT);
  for (const text of SWEDISH) {
    assert.equal([...text].every((character) => character.codePointAt(0) <= 0xff), true);
  }
});
