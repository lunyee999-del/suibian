import fs from "node:fs";
import path from "node:path";

export function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

export function writeJson(dirPath, fileName, payload) {
  ensureDir(dirPath);
  const target = path.join(dirPath, fileName);
  fs.writeFileSync(target, JSON.stringify(payload, null, 2), "utf8");
  return target;
}

