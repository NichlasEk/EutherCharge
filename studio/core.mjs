export const KNOWN_IMAGE_SIZE = 4 * 1024 * 1024;
export const KNOWN_SHA256 = "d369a860ae39b307ec9cdd00fb59b2501937a20f7f20d9417ff5eede83b841e2";
export const POINTER_BASE = 0x3200;
export const ENTRY_COUNT = 162;
export const HISTORY_OFFSET = 0x383000;
export const HISTORY_RECORD_SIZE = 52;

export const BANKS = Object.freeze([
  { name: "English", tableOffset: 0x3600, stringsOffset: 0x3888, editable: true },
  { name: "Français", tableOffset: 0x4356, stringsOffset: 0x45de, editable: true },
  { name: "Español", tableOffset: 0x546d, stringsOffset: 0x56f5, editable: true },
  { name: "Deutsch", tableOffset: 0x6443, stringsOffset: 0x66cb, editable: true },
  { name: "Russian-custom", tableOffset: 0x7415, stringsOffset: 0x769d, editable: false },
  { name: "Italiano", tableOffset: 0x843f, stringsOffset: 0x86c7, editable: true },
  { name: "Português", tableOffset: 0x9414, stringsOffset: 0x969c, editable: true },
  { name: "Nederlands", tableOffset: 0xa3f2, stringsOffset: 0xa67a, editable: true },
]);

const decoder = new TextDecoder("latin1");

export function hex(value, digits = 6) {
  return `0x${value.toString(16).toUpperCase().padStart(digits, "0")}`;
}

export function readU16BE(data, offset) {
  return (data[offset] << 8) | data[offset + 1];
}

export function readU32BE(data, offset) {
  return (((data[offset] * 0x1000000) + (data[offset + 1] << 16) +
    (data[offset + 2] << 8) + data[offset + 3]) >>> 0);
}

export function readU16LE(data, offset) {
  return data[offset] | (data[offset + 1] << 8);
}

export function readF32LE(data, offset) {
  return new DataView(data.buffer, data.byteOffset + offset, 4).getFloat32(0, true);
}

export function parseHistory(data) {
  const records = [];
  for (let index = 0; index < 64; index += 1) {
    const offset = HISTORY_OFFSET + index * HISTORY_RECORD_SIZE;
    if (offset + HISTORY_RECORD_SIZE > data.length) break;
    if (data[offset] === 0xff && data[offset + 1] === 0xff) break;
    if (data[offset + 1] !== 0xa5) throw new Error(`Historikpost #${index} saknar A5-markör`);
    records.push({
      index,
      offset,
      markerHex: `${data[offset].toString(16).padStart(2, "0")}${data[offset + 1].toString(16).padStart(2, "0")}`,
      modeByteCandidate: data[offset + 15],
      ratedValue: readU16LE(data, offset + 24),
      measuredValue: readU16LE(data, offset + 34),
      voltageRaw: readU16LE(data, offset + 36),
      voltage: readU16LE(data, offset + 36) / 100,
      healthPercent: readU16LE(data, offset + 38),
      chargePercent: readU16LE(data, offset + 40),
      resistance: readF32LE(data, offset + 44),
    });
  }
  return records;
}

export function parseBank(data, bank) {
  const entries = [];
  let previous = -1;
  for (let index = 0; index < ENTRY_COUNT; index += 1) {
    const pointerOffset = bank.tableOffset + index * 4;
    if (pointerOffset + 4 > data.length) throw new Error(`${bank.name}: pekartabellen går utanför filen`);
    const recordOffset = POINTER_BASE + readU32BE(data, pointerOffset);
    if (recordOffset < bank.stringsOffset || recordOffset <= previous) {
      throw new Error(`${bank.name}: ogiltig pekare #${index} → ${hex(recordOffset)}`);
    }
    if (recordOffset + 2 > data.length) throw new Error(`${bank.name}: post #${index} går utanför filen`);
    const allocation = readU16BE(data, recordOffset);
    const start = recordOffset + 2;
    const end = start + allocation;
    if (allocation < 1 || allocation > 256 || end > data.length) {
      throw new Error(`${bank.name}: ogiltig stränglängd vid #${index}`);
    }
    const raw = data.slice(start, end);
    if (raw[raw.length - 1] !== 0) throw new Error(`${bank.name}: post #${index} saknar NUL`);
    const firstNul = raw.indexOf(0);
    entries.push({
      language: bank.name,
      index,
      pointerOffset,
      recordOffset,
      payloadOffset: start,
      allocation,
      capacity: allocation - 1,
      text: decoder.decode(raw.slice(0, firstNul === -1 ? raw.length : firstNul)),
      editable: bank.editable,
    });
    previous = recordOffset;
  }
  return entries;
}

export function parseAllBanks(data) {
  return new Map(BANKS.map((bank) => [bank.name, parseBank(data, bank)]));
}

export function encodeLatin1(text) {
  const result = new Uint8Array(text.length);
  for (let index = 0; index < text.length; index += 1) {
    const code = text.codePointAt(index);
    if (code > 0xff) throw new Error(`Tecknet ${String.fromCodePoint(code)} finns inte i Latin-1`);
    result[index] = code;
  }
  return result;
}

export function applyFixedTextPatch(image, entry, text) {
  if (!entry.editable) throw new Error(`${entry.language} har ännu okänd teckenkodning`);
  const encoded = encodeLatin1(text);
  if (encoded.length > entry.capacity) {
    throw new Error(`${encoded.length} byte ryms inte i platsens ${entry.capacity} byte`);
  }
  const before = image.slice(entry.payloadOffset, entry.payloadOffset + entry.allocation);
  const after = new Uint8Array(entry.allocation);
  after.set(encoded, 0);
  // Uint8Array starts zero-filled: immediate terminator plus an inert tail.
  image.set(after, entry.payloadOffset);
  return {
    language: entry.language,
    index: entry.index,
    offset: entry.payloadOffset,
    allocation: entry.allocation,
    beforeText: entry.text,
    afterText: text,
    beforeHex: bytesToHex(before),
    afterHex: bytesToHex(after),
  };
}

export function bytesToHex(bytes) {
  return Array.from(bytes, (value) => value.toString(16).padStart(2, "0")).join("");
}

export async function digestHex(data) {
  const digest = await crypto.subtle.digest("SHA-256", data);
  return bytesToHex(new Uint8Array(digest));
}

export function getPixel(data, baseOffset, width, height, format, x, y) {
  if (x < 0 || y < 0 || x >= width || y >= height) return [0, 0, 0, 0];
  if (format === "mono-row-msb" || format === "mono-row-lsb") {
    const stride = Math.ceil(width / 8);
    const value = data[baseOffset + y * stride + Math.floor(x / 8)] ?? 0;
    const bit = format.endsWith("msb") ? 7 - (x % 8) : x % 8;
    return ((value >> bit) & 1) ? [255, 151, 27, 255] : [10, 15, 20, 255];
  }
  if (format === "mono-column-msb" || format === "mono-column-lsb") {
    const value = data[baseOffset + Math.floor(y / 8) * width + x] ?? 0;
    const bit = format.endsWith("msb") ? 7 - (y % 8) : y % 8;
    return ((value >> bit) & 1) ? [255, 151, 27, 255] : [10, 15, 20, 255];
  }
  if (format === "indexed8") {
    const value = data[baseOffset + y * width + x] ?? 0;
    return [value, value, value, 255];
  }
  if (format === "indexed4-high" || format === "indexed4-low") {
    const stride = Math.ceil(width / 2);
    const value = data[baseOffset + y * stride + Math.floor(x / 2)] ?? 0;
    const highFirst = format.endsWith("high");
    const highNibble = x % 2 === 0 ? highFirst : !highFirst;
    const index = highNibble ? value >> 4 : value & 0x0f;
    const level = index * 17;
    return [level, level, level, 255];
  }
  if (format === "indexed2-msb" || format === "indexed2-lsb") {
    const stride = Math.ceil(width / 4);
    const value = data[baseOffset + y * stride + Math.floor(x / 4)] ?? 0;
    const pair = x % 4;
    const shift = format.endsWith("msb") ? 6 - pair * 2 : pair * 2;
    const level = ((value >> shift) & 3) * 85;
    return [level, level, level, 255];
  }
  const offset = baseOffset + (y * width + x) * 2;
  const word = format === "rgb565be"
    ? (((data[offset] ?? 0) << 8) | (data[offset + 1] ?? 0))
    : (((data[offset + 1] ?? 0) << 8) | (data[offset] ?? 0));
  const red = Math.round(((word >> 11) & 31) * 255 / 31);
  const green = Math.round(((word >> 5) & 63) * 255 / 63);
  const blue = Math.round((word & 31) * 255 / 31);
  return [red, green, blue, 255];
}

export function requiredBytes(width, height, format) {
  if (format.startsWith("mono-row")) return Math.ceil(width / 8) * height;
  if (format.startsWith("mono-column")) return width * Math.ceil(height / 8);
  if (format.startsWith("indexed2")) return Math.ceil(width / 4) * height;
  if (format.startsWith("indexed4")) return Math.ceil(width / 2) * height;
  if (format === "indexed8") return width * height;
  return width * height * 2;
}
