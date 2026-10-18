import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const read = (path:string) => readFileSync(path, "utf8");

test("Blue independent atlas and modern sans identity replace Kerala2040 visual treatment", () => {
  const css = read("src/app/globals.css");
  assert.match(css, /--blue:\s*#003580/i);
  assert.match(css, /--surface:\s*#ffffff/i);
  assert.match(css, /Manrope/);
  assert.doesNotMatch(css, /Playfair Display|#f7f2e4|#b18843|#9e4e35/i);
  assert.match(css, /@media\(max-width:600px\)/);
  assert.match(css, /prefers-reduced-motion/);
});

test("original research brand uses a conceptual grid, not a map or a flag", () => {
  const home = read("src/app/page.tsx");
  const network = read("src/components/network-visual.tsx");
  const icon = read("src/app/icon.svg");
  const layout = read("src/app/layout.tsx");
  const og = read("src/app/opengraph-image.tsx");
  const mark = read("src/components/grid-mark.tsx");
  assert.match(home, /Grid evidence/);
  assert.match(home, /NetworkVisual/);
  assert.match(home, /Public snapshot mode/);
  assert.match(network, /NOT a map or electricity-network topology/);
  assert.match(network, /SOURCES → VALIDATION → SCREENING/);
  assert.match(icon, /independent network evidence/i);
  assert.match(mark, /network mark/i);
  assert.match(og, /ABSTRACT DATA NETWORK/);
  assert.doesNotMatch(layout + icon + network + og, /atlasRegions|Natural Earth|geographic boundaries|brand-cross|footer-cross|flag-like white cross/i);
  assert.match(layout, /Independent research platform/);
  assert.match(layout, /Not affiliated with a transmission system operator/);
});

test("navigable route and source links survive visual migration", () => {
  const layout = read("src/app/layout.tsx");
  const connections = read("src/app/connections/page.tsx");
  for (const path of ["/connections", "/operations", "/method", "/api"]) assert.ok(layout.includes(path), path);
  assert.match(connections, /Open filtered API JSON/);
  assert.match(connections, /Unknown|not imply zero capacity|not independently/i);
});
