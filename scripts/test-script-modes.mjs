// Tracked scripts under skills/ that start with a shebang must be recorded in
// the Git index as 100755. Otherwise every install route that copies the
// checked-out file (clone, tarball, ZIP) ships them non-executable, and skills
// that run ./scripts/<name>.sh fail with "Permission denied" on macOS and Linux.
//
//   node --test scripts/test-script-modes.mjs

import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import test from 'node:test';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');

function trackedFiles() {
  const out = execFileSync('git', ['ls-files', '-s', '-z', '--', 'skills'], { cwd: root, encoding: 'utf8' });
  return out
    .split('\0')
    .filter(Boolean)
    .map((entry) => {
      const [meta, file] = entry.split('\t');
      const [mode] = meta.split(' ');
      return { mode, file };
    });
}

function startsWithShebang(file) {
  const fd = fs.openSync(path.join(root, file), 'r');
  try {
    const buf = Buffer.alloc(2);
    const n = fs.readSync(fd, buf, 0, 2, 0);
    return n === 2 && buf[0] === 0x23 && buf[1] === 0x21;
  } finally {
    fs.closeSync(fd);
  }
}

test('tracked skill scripts with a shebang are indexed as executable', () => {
  const offenders = trackedFiles()
    .filter(({ mode, file }) => mode !== '100755' && startsWithShebang(file))
    .map(({ mode, file }) => `${mode} ${file}`);
  assert.equal(
    offenders.length,
    0,
    `${offenders.length} tracked shebang files under skills/ are not mode 100755:\n${offenders.join('\n')}`
  );
});
