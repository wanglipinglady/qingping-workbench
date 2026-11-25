#!/usr/bin/env node
import { readFileSync } from 'node:fs';
import { dirname, join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import semver from 'semver';

const scriptDir = dirname(fileURLToPath(import.meta.url));
const frontendDir = join(scriptDir, '..');
const lockPath = join(frontendDir, 'package-lock.json');
const lock = JSON.parse(readFileSync(lockPath, 'utf8'));
const packages = lock.packages || {};
const currentNode = process.version;
const incompatible = [];
let checked = 0;

for (const [packagePath, metadata] of Object.entries(packages)) {
  const range = metadata?.engines?.node;
  if (!range) continue;

  checked += 1;
  const validRange = semver.validRange(range);
  const compatible = validRange && semver.satisfies(currentNode, validRange, {
    includePrerelease: true,
  });

  if (!compatible) {
    incompatible.push({
      packagePath: packagePath || '(项目根包)',
      version: metadata.version || '(未知)',
      range,
      reason: validRange ? '版本不兼容' : 'engines.node 格式无效',
    });
  }
}

console.log(`[信息] 当前 Node: ${currentNode}`);
console.log(`[信息] 锁文件: ${relative(frontendDir, lockPath)}`);
console.log(`[信息] 已检查 ${checked} 个声明 engines.node 的锁定包`);

if (incompatible.length > 0) {
  console.error(`[错误] 发现 ${incompatible.length} 个与 ${currentNode} 不兼容的包：`);
  for (const item of incompatible) {
    console.error(
      `  - ${item.packagePath}@${item.version}: node ${item.range}（${item.reason}）`,
    );
  }
  process.exit(1);
}

console.log('[通过] package-lock.json 中所有已声明 Node 引擎的包均兼容');
