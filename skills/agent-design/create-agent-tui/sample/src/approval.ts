import { resolve, relative, isAbsolute } from 'path';
import type { ApprovalPolicy } from './config.js';

// Session-scoped cache: once the user approves a given tool+target, the same
// target is not re-prompted for the rest of the run. Cleared by /new.
const approved = new Set<string>();

export function resetApprovals(): void {
  approved.clear();
}

/** Shell commands that warrant a prompt even under 'dangerous-only'. */
const DESTRUCTIVE =
  /\brm\b|\bsudo\b|\bchmod\b|\bchown\b|\bdd\b|\bmkfs\b|\bkill(all)?\b|>\s*\/dev\/|\bgit\s+(push|reset\s+--hard|clean)\b|\bcurl\b[^|]*\|\s*(ba)?sh/;

export function isDestructiveCommand(command: string): boolean {
  return DESTRUCTIVE.test(command);
}

/** True when a write target escapes the working directory. */
export function escapesCwd(path: string): boolean {
  const rel = relative(process.cwd(), resolve(path));
  return rel.startsWith('..') || isAbsolute(rel);
}

export function needsApproval(policy: ApprovalPolicy, dangerous: boolean): boolean {
  if (policy === 'never') return false;
  if (policy === 'always') return true;
  return dangerous;
}

const DIM = '\x1b[2m';
const RESET = '\x1b[0m';
const YELLOW = '\x1b[33m';

/**
 * Read a single keypress in raw mode. The REPL releases stdin between turns
 * (see cli.ts), so this does not fight the input reader — and it deliberately
 * avoids opening a second readline interface, which would double-consume input.
 */
function readKey(): Promise<string> {
  return new Promise((res) => {
    const wasRaw = process.stdin.isRaw ?? false;
    if (process.stdin.isTTY) process.stdin.setRawMode(true);
    process.stdin.resume();
    const onData = (buf: Buffer) => {
      process.stdin.off('data', onData);
      if (process.stdin.isTTY) process.stdin.setRawMode(wasRaw);
      process.stdin.pause();
      const key = buf.toString('utf-8');
      if (key.charCodeAt(0) === 3) process.exit(130); // Ctrl+C
      res(key);
    };
    process.stdin.on('data', onData);
  });
}

/**
 * Prompt the user to confirm one tool call. Returns false to deny — callers
 * return an error to the model rather than throwing, so the agent can recover
 * and try something else.
 *
 * Non-interactive stdin denies by default: an unattended run must not silently
 * escalate to unprompted writes and shell commands.
 */
export async function confirm(tool: string, target: string, detail: string): Promise<boolean> {
  const key = `${tool}:${target}`;
  if (approved.has(key)) return true;

  if (!process.stdin.isTTY) return false;

  process.stdout.write(
    `\n  ${YELLOW}⚠${RESET}  ${tool} wants to ${detail}\n     ${DIM}[y] allow once  [a] allow for this session  [n] deny${RESET} `,
  );
  const choice = (await readKey()).trim().toLowerCase();
  process.stdout.write('\n');

  if (choice === 'a') {
    approved.add(key);
    return true;
  }
  return choice === 'y';
}
