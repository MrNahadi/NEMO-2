import esbuild from "../../app/node_modules/esbuild/lib/main.js";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const appDir = path.resolve(here, "../../app");

esbuild.buildSync({
  stdin: {
    contents: [
      'import * as React from "react";',
      'import * as ReactDOM from "react-dom/client";',
      "window.React = React;",
      "window.ReactDOM = ReactDOM;",
    ].join("\n"),
    resolveDir: appDir,
    loader: "js",
  },
  bundle: true,
  minify: true,
  format: "iife",
  define: { "process.env.NODE_ENV": '"production"' },
  outfile: path.join(here, "vendor/react-runtime.js"),
});

console.log("Built vendor/react-runtime.js");
