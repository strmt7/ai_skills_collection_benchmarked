const fs = require("node:fs");
const path = require("node:path");
const { test: base, expect } = require("@playwright/test");

const parent = process.env.CONTROL_PARENT;
const stage = process.env.CONTROL_STAGE;
const mode = process.env.CONTROL_MODE;

const test = base.extend({
  ownedDirectory: async ({}, use) => {
    const directory = fs.mkdtempSync(path.join(parent, "owned-"));
    fs.writeFileSync(path.join(parent, "allocation.txt"), path.basename(directory));
    const acquireSecondAndUse = async () => {
      if (stage === "setup") throw new Error("deliberate second acquisition failure");
      fs.writeFileSync(path.join(directory, "ready.txt"), "ready", { flag: "wx" });
      await use(directory);
    };
    if (mode === "missing-finally") {
      await acquireSecondAndUse();
      fs.rmSync(directory, { recursive: true });
    } else {
      try {
        await acquireSecondAndUse();
      } finally {
        fs.rmSync(directory, { recursive: true });
      }
    }
  }
});

test("uses the resource and records its state", async ({ ownedDirectory }) => {
  fs.writeFileSync(path.join(parent, "body-entered.txt"), "yes", { flag: "wx" });
  const value = fs.readFileSync(path.join(ownedDirectory, "ready.txt"), "utf8");
  expect(value, "intended behavior assertion").toBe(stage === "body" ? "incorrect" : "ready");
});
