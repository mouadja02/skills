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
| [`m-and-a-advisor`](./m-and-a-advisor/SKILL.md) | Strategic guidance and robust frameworks for managing Mergers and Acquisitions (M&A), due diligence, and post-merger integration. |

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

### Go-to-Market (GTM)

| Skill | What it does |
| --- | --- |
| [`gtm-0-to-1-launch`](./gtm-0-to-1-launch/SKILL.md) | Zero-to-one product launch playbook — ICP definition, messaging, launch sequencing. |
| [`gtm-ai-gtm`](./gtm-ai-gtm/SKILL.md) | AI-specific GTM strategy — developer adoption, API monetization, model differentiation. |
| [`gtm-board-and-investor-communication`](./gtm-board-and-investor-communication/SKILL.md) | Craft board updates and investor communications for GTM milestones. |
| [`gtm-developer-ecosystem`](./gtm-developer-ecosystem/SKILL.md) | Build developer ecosystems — SDKs, docs, community, developer relations. |
| [`gtm-enterprise-account-planning`](./gtm-enterprise-account-planning/SKILL.md) | Enterprise account planning — territory strategy, stakeholder mapping, expansion plays. |
| [`gtm-enterprise-onboarding`](./gtm-enterprise-onboarding/SKILL.md) | Design enterprise onboarding programs that drive time-to-value. |
| [`gtm-operating-cadence`](./gtm-operating-cadence/SKILL.md) | Establish GTM operating cadence — weekly/monthly/quarterly rituals and reviews. |
| [`gtm-partnership-architecture`](./gtm-partnership-architecture/SKILL.md) | Design partner programs — resellers, ISVs, technology alliances, channel strategy. |
| [`gtm-positioning-strategy`](./gtm-positioning-strategy/SKILL.md) | Develop product positioning and messaging frameworks for GTM. |
| [`gtm-product-led-growth`](./gtm-product-led-growth/SKILL.md) | PLG strategy — freemium design, activation funnels, viral loops, expansion revenue. |
| [`gtm-technical-product-pricing`](./gtm-technical-product-pricing/SKILL.md) | Price technical products — usage-based, seat-based, value metrics, packaging. |

### Career & personal effectiveness

| Skill | What it does |
| --- | --- |
| [`brag-sheet`](./brag-sheet/SKILL.md) | Turn vague accomplishments into evidence-backed impact statements for performance reviews and promotion packets. |
| [`impediment-prioritization`](./impediment-prioritization/SKILL.md) | Identify, prioritize, and plan removal of team impediments blocking delivery. |

## When to use this folder

- "Should I do X or Y?" (high-stakes business decision)
- "Help me prepare for the board meeting"
- "What does my CTO/CFO/CMO think about this?"
- "Run a 6-phase board deliberation on this question"
- "Audit our org health"
- "Stress-test this plan"
- "Build our GTM strategy" / "price this product" / "design a partner program"

## Related categories

- [`marketing-and-growth/`](../marketing-and-growth/) — tactical execution of the CMO and CRO strategies.
- [`product-management/`](../product-management/) — execution layer for the CPO advisor.
- [`devops-and-infrastructure/`](../devops-and-infrastructure/) — execution layer for the CTO advisor.
