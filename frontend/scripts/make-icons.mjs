import { writeFileSync, mkdirSync, existsSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const iconsDir = resolve(__dirname, "..", "src-tauri", "icons");
mkdirSync(iconsDir, { recursive: true });

const pngBase64 =
  "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==";
const png = Buffer.from(pngBase64, "base64");

const pngTargets = [
  "32x32.png",
  "128x128.png",
  "128x128@2x.png",
  "icon.png",
  "Square30x30Logo.png",
  "Square44x44Logo.png",
  "Square71x71Logo.png",
  "Square89x89Logo.png",
  "Square107x107Logo.png",
  "Square142x142Logo.png",
  "Square150x150Logo.png",
  "Square284x284Logo.png",
  "Square310x310Logo.png",
  "StoreLogo.png",
];

for (const name of pngTargets) {
  const p = resolve(iconsDir, name);
  if (!existsSync(p)) writeFileSync(p, png);
}

const icoHeader = Buffer.from([
  0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01, 0x00,
  0x20, 0x00,
]);
const icoSizeField = Buffer.alloc(8);
icoSizeField.writeUInt32LE(png.length, 0);
icoSizeField.writeUInt32LE(22, 4);
const ico = Buffer.concat([icoHeader, icoSizeField, png]);
const icoPath = resolve(iconsDir, "icon.ico");
if (!existsSync(icoPath)) writeFileSync(icoPath, ico);

const icnsPath = resolve(iconsDir, "icon.icns");
if (!existsSync(icnsPath)) writeFileSync(icnsPath, png);

console.log("placeholder icons written to", iconsDir);
