// Record the actual production module graph without changing application configuration.
import { build } from "vite";
import { mkdirSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

const output = process.argv[2];
if (!output) throw new Error("Provide a new output directory");
mkdirSync(output); // Refuse to overwrite prior evidence.
await build({
  root: "apps/desktop",
  build: { outDir: resolve(output, "ui"), emptyOutDir: false },
  plugins: [
    {
      name: "distribution-evidence",
      generateBundle() {
        const modules = [...this.getModuleIds()]
          .filter((id) => id.includes("/node_modules/"))
          .map((id) => id.slice(id.indexOf("node_modules/")))
          .sort();
        writeFileSync(
          resolve(output, "modules.json"),
          JSON.stringify(modules, null, 2) + "\n",
        );
      },
    },
  ],
});
