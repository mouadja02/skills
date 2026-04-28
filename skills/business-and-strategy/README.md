# business-and-strategy

The **C-suite advisor system** plus strategic-ops skills for founders, executives, and operators. A coherent multi-agent setup where 10 executive personas can be queried individually, orchestrated through a chief-of-staff, or convened in a structured board meeting.

> Most of these skills read company context from `~/.claude/company-context.md`. Run `cs-onboard` once to generate that file before relying on the advisors.

## Skills in this category

### Foundation (run first)

| Skill | What it does |
| --- | --- |
| [`cs-onboard`](./cs-onboard/SKILL.md) | Founder onboarding interview. Captures company context across 7 dimensions and writes `~/.claude/company-context.md`. Run with `/cs:setup` initially or `/cs:update` quarterly. |
| [`context-engine`](./context-engine/SKILL.md) | Loads & manages company context for all C-suite advisor skills. Detects stale context (>90 days), enriches during conversation, enforces privacy/anonymization before external API calls. |

### C-suite advisor personas

| Skill | What it does |
| --- | --- |
| [`ceo-advisor`](./ceo-advisor/SKILL.md) | Executive leadership — strategy, board prep, investor management, organizational development. |
| [`cto-advisor`](./cto-advisor/SKILL.md) | Technical leadership — architecture decisions, engineering scaling, tech debt, technology strategy. |
| [`cfo-advisor`](./cfo-advisor/SKILL.md) | Financial leadership — financial models, unit economics, fundraising, cash management, board financial packages. |
| [`coo-advisor`](./coo-advisor/SKILL.md) | Operations leadership — process design, OKR execution, operational cadence, scaling playbooks. |
| [`cmo-advisor`](./cmo-advisor/SKILL.md) | Marketing leadership — brand positioning, growth model design (PLG vs sales-led vs community), budget allocation. |
| [`cpo-advisor`](./cpo-advisor/SKILL.md) | Product leadership — product vision, portfolio strategy, PMF measurement, product org design. |
| [`cro-advisor`](./cro-advisor/SKILL.md) | Revenue leadership for B2B SaaS — forecasting, sales model, pricing, NRR, sales scaling. |
| [`ciso-advisor`](./ciso-advisor/SKILL.md) | Security leadership — risk in dollars, compliance roadmap (SOC 2/ISO 27001/HIPAA/GDPR), incident response, board security reporting. |
| [`chro-advisor`](./chro-advisor/SKILL.md) | People leadership — hiring strategy, comp design, org structure, culture, retention. |

### Orchestration

| Skill | What it does |
| --- | --- |
| [`c-level-advisor`](./c-level-advisor/SKILL.md) | Channels all 10 executive perspectives (the 9 above + executive-mentor) across decisions and trade-offs. Routes to the right advisor or runs multi-role analyses. |
| [`chief-of-staff`](./chief-of-staff/SKILL.md) | C-suite orchestration layer. Routes founder questions to the right advisor, triggers multi-role board meetings for complex decisions, synthesizes outputs, tracks decisions. The default entry point. |
| [`executive-mentor`](./executive-mentor/SKILL.md) | Adversarial thinking partner. Stress-tests plans, prepares for brutal board meetings, dissects no-good-options decisions, forces honest post-mortems. |
| [`board-meeting`](./board-meeting/SKILL.md) | Multi-agent board meeting protocol. 6-phase deliberation: context loading → independent C-suite contributions (isolated) → critic analysis → synthesis → founder review → decision extraction. |
| [`board-deck-builder`](./board-deck-builder/SKILL.md) | Assembles board / investor update decks by pulling perspectives from all C-suite roles. For board meetings, QBRs, fundraising narratives. |
| [`decision-logger`](./decision-logger/SKILL.md) | Two-layer memory architecture for board decisions. Manages raw transcripts (Layer 1) and approved decisions (Layer 2). Track overdue action items via `/cs:decisions`. |

### Frameworks & diagnostics

| Skill | What it does |
| --- | --- |
| [`company-os`](./company-os/SKILL.md) | The meta-framework for how a company runs — operating system selection (EOS, Scaling Up, OKR-native, hybrid), accountability charts, scorecards, meeting pulse, 90-day rocks. |
| [`scenario-war-room`](./scenario-war-room/SKILL.md) | Cross-functional what-if modeling for cascading multi-variable scenarios. Models compound adversity across all business functions simultaneously. |
| [`org-health-diagnostic`](./org-health-diagnostic/SKILL.md) | Cross-functional health check combining signals from all C-suite roles. Scores 8 dimensions on a traffic-light scale with drill-down recommendations. |
| [`saas-metrics-coach`](./saas-metrics-coach/SKILL.md) | SaaS financial health advisor. Use when sharing revenue or customer numbers — ARR, MRR, churn, LTV, CAC, NRR. |
| [`cs-founder-coach`](./cs-founder-coach/SKILL.md) | Personal leadership development for founders and first-time CEOs. Founder archetypes, delegation, energy management, calendar audits, blind spots, imposter syndrome. |

## When to use this folder

- "Should I do X or Y?" (high-stakes business decision)
- "Help me prepare for the board meeting"
- "What does my CTO/CFO/CMO think about this?"
- "Run a 6-phase board deliberation on this question"
- "Audit our org health"
- "Stress-test this plan"

## Related categories

- [`marketing-and-growth/`](../marketing-and-growth/) — tactical execution of the CMO and CRO strategies.
- [`product-management/`](../product-management/) — execution layer for the CPO advisor.
- [`devops-and-infrastructure/`](../devops-and-infrastructure/) — execution layer for the CTO advisor.
