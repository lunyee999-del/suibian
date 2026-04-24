import fs from "node:fs";
import path from "node:path";

export function ensureProfileDir(profileDir) {
  fs.mkdirSync(profileDir, { recursive: true });
  return path.resolve(profileDir);
}

