import { serverTool } from '@openrouter/agent';
import type { AgentConfig } from '../config.js';
import { fileReadTool } from './file-read.js';
import { createFileWriteTool } from './file-write.js';
import { createFileEditTool } from './file-edit.js';
import { globTool } from './glob.js';
import { grepTool } from './grep.js';
import { listDirTool } from './list-dir.js';
import { createShellTool } from './shell.js';

export function buildTools(config: AgentConfig) {
  return [
    // Read-only — never gated
    fileReadTool,
    globTool,
    grepTool,
    listDirTool,

    // Mutating — gated by config.approvalPolicy
    createFileWriteTool(config.approvalPolicy),
    createFileEditTool(config.approvalPolicy),
    createShellTool(config.approvalPolicy),

    serverTool({ type: 'openrouter:web_search' }),
    serverTool({ type: 'openrouter:datetime', parameters: { timezone: 'UTC' } }),
  ];
}
