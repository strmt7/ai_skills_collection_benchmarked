/** Static JavaScript/TypeScript documentation candidates; never imports target code. */
import { parse } from "@babel/parser";
import { createHash, randomUUID } from "node:crypto";
import { readFileSync, readdirSync, realpathSync, renameSync, statSync, unlinkSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const METHODS = new Set(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]);
const EXTENSIONS = new Set([".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"]);
const SKIP = new Set([".git", ".next", ".venv", "venv", "node_modules", "__pycache__"]);

function literal(node) {
  if (node?.type === "StringLiteral") return node.value;
  if (node?.type === "TemplateLiteral" && node.expressions.length === 0) return node.quasis[0].value.cooked;
  return null;
}

function functionHeader(node, text) {
  const end = node.body?.start ?? node.end;
  return text.slice(node.start, end).trim();
}

function nextPath(file) {
  const parts = file.split("/");
  const appIndex = parts[0] === "app" ? 0 : parts[0] === "src" && parts[1] === "app" ? 1 : -1;
  if (appIndex < 0 || !["route.js", "route.ts"].includes(parts.at(-1))) return null;
  const segments = parts.slice(appIndex + 1, -1);
  if (segments.some((segment) => segment.startsWith("_"))) return null;
  if (segments.some((segment) => segment.startsWith("@") || /^\(\.{1,3}\)/u.test(segment))) {
    return { path: null, resolution: "unresolved" };
  }
  const retained = segments.filter((segment) => !/^\([^/]+\)$/u.test(segment));
  return { path: `/${retained.join("/")}`, resolution: "filesystem_pattern" };
}

function inspectFile(tree, file, text, isNext) {
  const factories = new Set();
  const routerFactories = new Set();
  const bindings = new Map();
  const pending = [];
  const mounts = [];
  const functions = [];
  const types = [];
  const nextRoutes = [];
  const routePattern = isNext ? nextPath(file) : null;
  const forget = (name) => { factories.delete(name); routerFactories.delete(name); bindings.delete(name); };

  function recordExport(declaration, isDefault = false) {
    if (!declaration) return;
    if (declaration.type === "FunctionDeclaration") {
      const name = declaration.id?.name ?? "default";
      functions.push({ name, signature: functionHeader(declaration, text), file, line: declaration.loc.start.line });
      if (!isDefault && routePattern && METHODS.has(name)) {
        nextRoutes.push({ framework: "nextjs", method: name, ...routePattern, handler: name, file, line: declaration.loc.start.line });
      }
    } else if (declaration.type === "VariableDeclaration") {
      for (const variable of declaration.declarations) {
        const name = variable.id?.type === "Identifier" ? variable.id.name : null;
        if (!name || !["ArrowFunctionExpression", "FunctionExpression"].includes(variable.init?.type)) continue;
        functions.push({ name, signature: functionHeader(variable.init, text), file, line: variable.loc.start.line });
        if (routePattern && METHODS.has(name)) {
          nextRoutes.push({ framework: "nextjs", method: name, ...routePattern, handler: name, file, line: variable.loc.start.line });
        }
      }
    } else if (["TSInterfaceDeclaration", "TSTypeAliasDeclaration", "TSEnumDeclaration", "ClassDeclaration"].includes(declaration.type)) {
      const name = declaration.id?.name ?? "default";
      types.push({ name, kind: declaration.type, definition: text.slice(declaration.start, declaration.end), file, line: declaration.loc.start.line });
    }
  }

  for (const statement of tree.program.body) {
    if (statement.type === "ImportDeclaration") {
      for (const specifier of statement.specifiers) {
        const name = specifier.local.name;
        forget(name);
        if (statement.source.value === "express") {
          if (specifier.type === "ImportDefaultSpecifier" && statement.importKind !== "type") factories.add(name);
          if (statement.importKind !== "type" && specifier.importKind !== "type" &&
              specifier.type === "ImportSpecifier" && specifier.imported.name === "Router") routerFactories.add(name);
        }
      }
      continue;
    }
    if (statement.type === "ExportNamedDeclaration" || statement.type === "ExportDefaultDeclaration") {
      recordExport(statement.declaration, statement.type === "ExportDefaultDeclaration");
      if (routePattern && statement.type === "ExportNamedDeclaration" && statement.exportKind !== "type") {
        for (const specifier of statement.specifiers) {
          const method = specifier.exported?.name;
          if (specifier.exportKind !== "type" && METHODS.has(method)) {
            nextRoutes.push({ framework: "nextjs", method, ...routePattern, handler: specifier.local?.name ?? null, file, line: specifier.loc.start.line });
          }
        }
      }
    }
    const declaration = statement.type === "ExportNamedDeclaration" ? statement.declaration : statement;
    if (declaration?.type === "VariableDeclaration") {
      for (const variable of declaration.declarations) {
        const init = variable.init;
        if (variable.id.type === "ObjectPattern" && init?.type === "CallExpression" && init.callee.type === "Identifier" &&
            init.callee.name === "require" && literal(init.arguments[0]) === "express") {
          for (const property of variable.id.properties) {
            if (property.type === "ObjectProperty" && property.key.name === "Router" && property.value.type === "Identifier") {
              forget(property.value.name); routerFactories.add(property.value.name);
            }
          }
          continue;
        }
        if (variable.id.type !== "Identifier") continue;
        const name = variable.id.name;
        const prior = init?.type === "Identifier" ? bindings.get(init.name) : undefined;
        let kind = null;
        if (init?.type === "CallExpression") {
          const callee = init.callee;
          if (callee.type === "Identifier" && factories.has(callee.name)) kind = "app";
          if (callee.type === "Identifier" && routerFactories.has(callee.name)) kind = "router";
          if (callee.type === "MemberExpression" && !callee.computed && callee.object.type === "Identifier" &&
              factories.has(callee.object.name) && callee.property.name === "Router") kind = "router";
        }
        forget(name);
        if (init?.type === "CallExpression" && init.callee.type === "Identifier" && init.callee.name === "require" &&
            literal(init.arguments[0]) === "express") factories.add(name);
        else if (kind) bindings.set(name, { kind });
        else if (prior) bindings.set(name, prior);
      }
      continue;
    }
    if (declaration?.type === "FunctionDeclaration" || declaration?.type === "ClassDeclaration") {
      if (declaration.id) forget(declaration.id.name);
      continue;
    }
    if (statement.type !== "ExpressionStatement") {
      // A conditional or other compound statement may reassign a tracked name.
      const visit = (node) => {
        if (!node || typeof node !== "object") return;
        if ((node.type === "AssignmentExpression" || node.type === "UpdateExpression") &&
            (node.left ?? node.argument)?.type === "Identifier") forget((node.left ?? node.argument).name);
        for (const value of Object.values(node)) {
          if (Array.isArray(value)) value.forEach(visit);
          else if (value && typeof value === "object") visit(value);
        }
      };
      visit(statement);
      continue;
    }
    const expression = statement.expression;
    if (expression.type === "AssignmentExpression" && expression.left.type === "Identifier") {
      forget(expression.left.name);
      continue;
    }
    if (expression.type !== "CallExpression" || expression.callee.type !== "MemberExpression" ||
        expression.callee.object.type !== "Identifier") continue;
    const receiverName = expression.callee.object.name;
    const receiver = bindings.get(receiverName);
    const property = expression.callee.computed ? literal(expression.callee.property) : expression.callee.property.name;
    if (!receiver || typeof property !== "string") continue;
    const args = expression.arguments;
    if (property === property.toLowerCase() && METHODS.has(property.toUpperCase()) && args.length >= 2) {
      const item = { framework: "express", receiver: receiverName, method: property.toUpperCase(), local_path: literal(args[0]), handler: args[1]?.type === "Identifier" ? args[1].name : null, file, line: expression.loc.start.line };
      pending.push({ receiver, item });
    } else if (property === "use" && receiver.kind === "app") {
      const first = args[0];
      const prefix = first?.type === "Identifier" && bindings.get(first.name)?.kind === "router" ? "" : literal(first);
      const rest = prefix === "" && first?.type === "Identifier" ? args : args.slice(1);
      for (const candidate of rest) {
        if (candidate?.type === "Identifier" && bindings.get(candidate.name)?.kind === "router") {
          mounts.push({ receiver: bindings.get(candidate.name), prefix, line: expression.loc.start.line });
        }
      }
    }
  }
  const routes = [...nextRoutes];
  for (const { receiver, item } of pending) {
    if (receiver.kind === "app") {
      routes.push({ ...item, path: item.local_path, resolution: item.local_path === null ? "unresolved" : "direct" });
      continue;
    }
    const matches = mounts.filter((mount) => mount.receiver === receiver);
    if (!matches.length) routes.push({ ...item, path: null, resolution: "unresolved" });
    for (const mount of matches) {
      const resolved = mount.prefix === null || item.local_path === null ? null :
        mount.prefix.endsWith("/") && item.local_path.startsWith("/") ? mount.prefix.slice(0, -1) + item.local_path :
        mount.prefix + item.local_path;
      routes.push({ ...item, path: resolved, resolution: resolved === null ? "unresolved" : "same_file_mount", mount_line: mount.line });
    }
  }
  return { functions, types, routes };
}

function filesUnder(root) {
  const files = [];
  function visit(directory) {
    for (const entry of readdirSync(directory, { withFileTypes: true }).sort((a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0)) {
      const full = path.join(directory, entry.name);
      if (entry.isDirectory() && !SKIP.has(entry.name)) visit(full);
      else if (entry.isFile() && EXTENSIONS.has(path.extname(entry.name))) files.push(full);
    }
  }
  visit(root);
  return files;
}

export function inventory(projectRoot) {
  const root = realpathSync(projectRoot);
  if (!statSync(root).isDirectory()) throw new Error("project root must be a directory");
  let isNext = false;
  try {
    const pkg = JSON.parse(readFileSync(path.join(root, "package.json"), "utf8"));
    isNext = Boolean(pkg.dependencies?.next || pkg.devDependencies?.next);
  } catch (error) {
    if (error.code !== "ENOENT") throw error;
  }
  const files = [];
  const functions = [];
  const types = [];
  const routes = [];
  for (const full of filesUnder(root)) {
    const relative = path.relative(root, full).split(path.sep).join("/");
    const bytes = readFileSync(full);
    const text = new TextDecoder("utf-8", { fatal: true }).decode(bytes);
    const ext = path.extname(full);
    const plugins = ["decorators"];
    if ([".ts", ".tsx", ".mts", ".cts"].includes(ext)) plugins.push("typescript");
    if ([".js", ".jsx", ".tsx"].includes(ext)) plugins.push("jsx");
    const tree = parse(text, { sourceType: "unambiguous", plugins, errorRecovery: false, sourceFilename: relative });
    const found = inspectFile(tree, relative, text, isNext);
    files.push({ file: relative, sha256: createHash("sha256").update(bytes).digest("hex") });
    functions.push(...found.functions); types.push(...found.types); routes.push(...found.routes);
  }
  return {
    schema_version: 1,
    kind: "static_candidates",
    limitations: [
      "Selected top-level exported functions and types, Express declarations and Next.js App Router conventions only.",
      "Cross-file, nested, dynamic, conditional and other framework routing can be missing or unresolved.",
      "Path patterns are source-derived candidates, not proof of runtime behavior or a complete API contract.",
    ],
    skipped_directories: [...SKIP].sort(),
    files, functions, types, routes,
  };
}

function main(argv) {
  if (argv.length !== 2) throw new Error("Usage: node inventory.mjs <project-root> <output.json>");
  const root = realpathSync(argv[0]);
  const output = path.resolve(argv[1]);
  const result = inventory(root);
  const relativeOutput = path.relative(root, output);
  const inside = relativeOutput !== ".." && !relativeOutput.startsWith(`..${path.sep}`) && !path.isAbsolute(relativeOutput);
  if (result.files.some((item) => path.resolve(root, item.file) === output) ||
      (EXTENSIONS.has(path.extname(output)) && inside)) {
    throw new Error("output must not replace a source file in the project");
  }
  const temporary = path.join(path.dirname(output), `.ts-inventory-${randomUUID()}.tmp`);
  try {
    writeFileSync(temporary, JSON.stringify(result, null, 2) + "\n", { encoding: "utf8", flag: "wx" });
    renameSync(temporary, output);
  } finally {
    try { unlinkSync(temporary); } catch (error) { if (error.code !== "ENOENT") throw error; }
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  try { main(process.argv.slice(2)); }
  catch (error) { console.error(`Inventory failed: ${error.message}`); process.exitCode = 2; }
}
