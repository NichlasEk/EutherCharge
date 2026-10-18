export const LOGO_WIDTH = 128;
export const LOGO_HEIGHT = 32;
export const LOGO_OFFSET = 0;
export const LOGO_SIZE = 512;

const FONT = Object.freeze({
  A: ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
  C: ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
  E: ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
  G: ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
  H: ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
  R: ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
  T: ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
  U: ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
});

function drawText(pixels, text, x, y, scale = 2) {
  for (const character of text) {
    const glyph = FONT[character];
    if (!glyph) throw new Error(`Missing logo glyph: ${character}`);
    glyph.forEach((row, gy) => [...row].forEach((value, gx) => {
      if (value !== "1") return;
      for (let sy = 0; sy < scale; sy += 1) for (let sx = 0; sx < scale; sx += 1) {
        const px = x + gx * scale + sx;
        const py = y + gy * scale + sy;
        if (px >= 0 && px < LOGO_WIDTH && py >= 0 && py < LOGO_HEIGHT) pixels[py * LOGO_WIDTH + px] = 1;
      }
    }));
    x += 6 * scale;
  }
}

export function generateEutherChargeLogo() {
  const pixels = new Uint8Array(LOGO_WIDTH * LOGO_HEIGHT);
  drawText(pixels, "EUTHER", 28, 1, 2);
  drawText(pixels, "CHARGE", 28, 17, 2);
  // Signature lightning marks. They fit outside the two 72-pixel word blocks.
  const bolt = [[13, 3], [12, 4], [11, 5], [10, 6], [9, 7], [12, 7], [10, 11], [15, 6], [12, 6], [14, 2]];
  for (const [x, y] of bolt) {
    pixels[y * LOGO_WIDTH + x] = 1;
    pixels[(LOGO_HEIGHT - 1 - y) * LOGO_WIDTH + (LOGO_WIDTH - 1 - x)] = 1;
  }
  return pixels;
}

export function decodeColumnLsb(data, offset = LOGO_OFFSET, width = LOGO_WIDTH, height = LOGO_HEIGHT) {
  const pixels = new Uint8Array(width * height);
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    pixels[y * width + x] = (data[offset + Math.floor(y / 8) * width + x] >> (y % 8)) & 1;
  }
  return pixels;
}

export function encodeColumnLsb(pixels, width = LOGO_WIDTH, height = LOGO_HEIGHT) {
  if (pixels.length !== width * height) throw new Error("Bitmap size does not match dimensions");
  const data = new Uint8Array(width * Math.ceil(height / 8));
  for (let y = 0; y < height; y += 1) for (let x = 0; x < width; x += 1) {
    if (pixels[y * width + x]) data[Math.floor(y / 8) * width + x] |= 1 << (y % 8);
  }
  return data;
}
