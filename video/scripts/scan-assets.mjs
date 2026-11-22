// Liste les fichiers présents dans /assets pour que la vidéo sache
// quels médias sont fournis et lesquels doivent rester en repère (placeholder).
import { readdirSync, statSync, writeFileSync, mkdirSync } from "node:fs";
import { join, relative, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, "..", "..", "assets");
const out = join(here, "..", "src", "generated", "assets.json");

const walk = (dir) =>
  readdirSync(dir).flatMap((name) => {
    if (name.startsWith(".")) return [];
    const p = join(dir, name);
    return statSync(p).isDirectory() ? walk(p) : [relative(root, p).split("\\").join("/")];
  });

const files = walk(root).sort();
mkdirSync(dirname(out), { recursive: true });
writeFileSync(out, JSON.stringify({ files }, null, 2) + "\n");
console.log(`assets: ${files.length} fichier(s) détecté(s)`);
for (const f of files) console.log("  · " + f);
