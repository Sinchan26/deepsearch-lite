import { compile } from "json-schema-to-typescript";
import { readFile, writeFile } from "node:fs/promises";
const schema = JSON.parse(await readFile(new URL("../../contracts/public-event.schema.json", import.meta.url), "utf8"));
const text = await compile(schema, "PublicEvent", { bannerComment: "/* Generated from Pydantic. Do not edit. */", additionalProperties: false });
const target = new URL("../src/contracts/public-event.ts", import.meta.url);
if (process.argv.includes("--check")) {
  if (await readFile(target, "utf8") !== text) throw new Error("Stale TypeScript contracts");
  console.log("TypeScript contracts match Pydantic schema");
} else await writeFile(target, text);
