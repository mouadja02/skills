import { tool } from '@openrouter/agent/tool';
import { z } from 'zod';
import { execFile } from 'child_process';
import { promisify } from 'util';
import { confirm, needsApproval, isDestructiveCommand } from '../approval.js';
import type { ApprovalPolicy } from '../config.js';

const execFileAsync = promisify(execFile);

export function createShellTool(policy: ApprovalPolicy) {
  return tool({
    name: 'shell',
    description: 'Execute a shell command and return output',
    inputSchema: z.object({
      command: z.string().describe('Shell command to execute'),
      timeout: z.number().optional().describe('Timeout in seconds (default: 120)'),
    }),
    requireApproval:
      policy === 'never' ? false : policy === 'always' ? true : ({ command }) => isDestructiveCommand(command),
    execute: async ({ command, timeout }) => {
      if (needsApproval(policy, isDestructiveCommand(command))) {
        const ok = await confirm('shell', command, `run: ${command}`);
        if (!ok) return { output: '', exitCode: null, denied: true, error: 'Denied by user. Do not retry this command.' };
      }

      const timeoutMs = (timeout ?? 120) * 1000;
      const shell = process.env.SHELL || '/bin/bash';

      try {
        const { stdout, stderr } = await execFileAsync(shell, ['-c', command], {
          timeout: timeoutMs,
          maxBuffer: 256 * 1024,
        });
        const output = (stdout + stderr).trim();
        const lines = output.split('\n');
        const truncated = lines.length > 2000;
        return {
          output: truncated ? lines.slice(-2000).join('\n') : output,
          exitCode: 0,
          ...(truncated && { truncated: true }),
        };
      } catch (err: any) {
        if (err.killed) {
          return { output: err.stdout?.trim() ?? '', exitCode: null, timedOut: true };
        }
        return {
          output: ((err.stdout ?? '') + (err.stderr ?? '')).trim(),
          exitCode: err.code ?? 1,
        };
      }
    },
  });
}
