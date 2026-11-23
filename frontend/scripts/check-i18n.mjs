/**
 * Pruebas de catálogo (R-IDI-03, R-IDI-04). Sin dependencias: `node scripts/check-i18n.mjs`.
 * - test_i18n_catalogs_complete: todos los catálogos cargados tienen exactamente las mismas claves.
 * - test_i18n_no_literal_strings: ningún texto visible escrito a mano dentro del JSX.
 */
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

const root = new URL("../src/", import.meta.url).pathname;
const keysOf = (file) => new Set([...readFileSync(join(root, "lib/i18n", file), "utf8").matchAll(/^\s+"([^"]+)":/gm)].map((m) => m[1]));
let failed = 0;
const fail = (test, msg) => {
  failed++;
  console.error(`FALLA ${test}: ${msg}`);
};

// test_i18n_catalogs_complete
const es = keysOf("es.ts");
for (const file of readdirSync(join(root, "lib/i18n")).filter((f) => /^[a-z]{2}\.ts$/.test(f) && f !== "es.ts")) {
  const other = keysOf(file);
  const missing = [...es].filter((k) => !other.has(k));
  const extra = [...other].filter((k) => !es.has(k));
  if (missing.length || extra.length) fail("test_i18n_catalogs_complete", `${file}: faltan ${missing.join(", ") || "—"}; sobran ${extra.join(", ") || "—"}`);
}

// test_i18n_no_literal_strings: texto con letras entre > y < en .tsx (se ignoran hanzi de ejemplo y símbolos)
const walk = (dir) => readdirSync(dir).flatMap((f) => (statSync(join(dir, f)).isDirectory() ? walk(join(dir, f)) : [join(dir, f)]));
for (const file of walk(root).filter((f) => f.endsWith(".tsx"))) {
  const src = readFileSync(file, "utf8");
  for (const m of src.matchAll(/>\s*([A-Za-zÁÉÍÓÚáéíóúÑñ][^<>{}]*[A-Za-z][^<>{}]*)\s*</g)) {
    const text = m[1].trim();
    if (/[;=()]|=>|&&|\|\|/.test(text)) continue; // código entre genéricos o comparaciones, no texto
    const tagStart = src.lastIndexOf("<", m.index);
    if (/\blang="zh/.test(src.slice(tagStart, m.index + 1))) continue; // contenido en chino (pinyin), no interfaz
    fail("test_i18n_no_literal_strings", `${file.replace(root, "src/")}: «${text.slice(0, 60)}»`);
  }
}

console.log(failed ? `${failed} fallos` : `OK · ${es.size} claves en cada catálogo, sin textos fuera de los catálogos`);
process.exit(failed ? 1 : 0);
