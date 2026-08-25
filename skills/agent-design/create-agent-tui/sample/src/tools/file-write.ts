import { tool } from '@openrouter/agent/tool';
import { z } from 'zod';
import { writeFile, mkdir } from 'fs/promises';
import { dirname } from 'path';
import { confirm, needsApproval, escapesCwd } from '../approval.js';
import type { ApprovalPolicy } from '../config.js';

export function createFileWriteTool(policy: ApprovalPolicy) {
  return tool({
    name: 'file_write',
    description: 'Write content to a file, creating it and parent directories if needed',
    inputSchema: z.object({
      path: z.string().describe('Absolute path to the file'),
      content: z.string().describe('Content to write'),
    }),
    requireApproval:
      policy === 'never' ? false : policy === 'always' ? true : ({ path }) => escapesCwd(path),
    execute: async ({ path, content }) => {
      if (needsApproval(policy, escapesCwd(path))) {
        const ok = await confirm('file_write', path, `write: ${path}`);
        if (!ok) return { error: 'Denied by user. Do not retry this write.' };
      }

      try {
        await mkdir(dirname(path), { recursive: true });
        await writeFile(path, content, 'utf-8');
        return { written: true, path };
      } catch (err: any) {
        return { error: err.message };
      }
    },
  });
}
