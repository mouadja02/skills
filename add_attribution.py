#!/usr/bin/env python3
"""
Apply source attribution to skill SKILL.md files.
Run: python add_attribution.py [group]
Groups: gsap, arize, qdrant, openrouter, streamlit, bmad, superpowers, copilot, microsoft, azure, context, all
"""

import sys
import os
import re

BASE = r"C:\Users\mouad\Desktop\skills\skills"

# Map: skill folder name -> (source_url, attribution_text, creator_url, creator_name)
SOURCE_MAP = {
    # ── greensock/gsap-skills ──────────────────────────────────────────────
    "gsap-core":                   ("https://github.com/greensock/gsap-skills", "greensock/gsap-skills", "https://greensock.com", "GreenSock"),
    "gsap-framer-scroll-animation":("https://github.com/greensock/gsap-skills", "greensock/gsap-skills", "https://greensock.com", "GreenSock"),
    "gsap-frameworks":             ("https://github.com/greensock/gsap-skills", "greensock/gsap-skills", "https://greensock.com", "GreenSock"),
    "gsap-performance":            ("https://github.com/greensock/gsap-skills", "greensock/gsap-skills", "https://greensock.com", "GreenSock"),
    "gsap-plugins":                ("https://github.com/greensock/gsap-skills", "greensock/gsap-skills", "https://greensock.com", "GreenSock"),
    "gsap-react":                  ("https://github.com/greensock/gsap-skills", "greensock/gsap-skills", "https://greensock.com", "GreenSock"),
    "gsap-scrolltrigger":          ("https://github.com/greensock/gsap-skills", "greensock/gsap-skills", "https://greensock.com", "GreenSock"),
    "gsap-timeline":               ("https://github.com/greensock/gsap-skills", "greensock/gsap-skills", "https://greensock.com", "GreenSock"),
    "gsap-utils":                  ("https://github.com/greensock/gsap-skills", "greensock/gsap-skills", "https://greensock.com", "GreenSock"),

    # ── Arize-ai/arize-skills ─────────────────────────────────────────────
    "arize-ai-provider-integration":("https://github.com/Arize-ai/arize-skills", "Arize-ai/arize-skills", "https://arize.com", "Arize AI"),
    "arize-annotation":            ("https://github.com/Arize-ai/arize-skills", "Arize-ai/arize-skills", "https://arize.com", "Arize AI"),
    "arize-dataset":               ("https://github.com/Arize-ai/arize-skills", "Arize-ai/arize-skills", "https://arize.com", "Arize AI"),
    "arize-evaluator":             ("https://github.com/Arize-ai/arize-skills", "Arize-ai/arize-skills", "https://arize.com", "Arize AI"),
    "arize-experiment":            ("https://github.com/Arize-ai/arize-skills", "Arize-ai/arize-skills", "https://arize.com", "Arize AI"),
    "arize-instrumentation":       ("https://github.com/Arize-ai/arize-skills", "Arize-ai/arize-skills", "https://arize.com", "Arize AI"),
    "arize-link":                  ("https://github.com/Arize-ai/arize-skills", "Arize-ai/arize-skills", "https://arize.com", "Arize AI"),
    "arize-prompt-optimization":   ("https://github.com/Arize-ai/arize-skills", "Arize-ai/arize-skills", "https://arize.com", "Arize AI"),
    "arize-trace":                 ("https://github.com/Arize-ai/arize-skills", "Arize-ai/arize-skills", "https://arize.com", "Arize AI"),

    # ── Arize-ai/phoenix ──────────────────────────────────────────────────
    "phoenix-cli":                 ("https://github.com/Arize-ai/phoenix", "Arize-ai/phoenix", "https://arize.com", "Arize AI"),
    "phoenix-evals":               ("https://github.com/Arize-ai/phoenix", "Arize-ai/phoenix", "https://arize.com", "Arize AI"),
    "phoenix-tracing":             ("https://github.com/Arize-ai/phoenix", "Arize-ai/phoenix", "https://arize.com", "Arize AI"),

    # ── qdrant/skills ─────────────────────────────────────────────────────
    "qdrant-clients-sdk":                    ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-deployment-options":             ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-model-migration":                ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-monitoring-debugging":           ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-monitoring-setup":               ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-monitoring":                     ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-indexing-performance-optimization":("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-memory-usage-optimization":      ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-search-speed-optimization":      ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-performance-optimization":       ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-minimize-latency":               ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-horizontal-scaling":             ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-scaling-data-volume":            ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-sliding-time-window":            ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-tenant-scaling":                 ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-vertical-scaling":               ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-scaling-qps":                    ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-scaling-query-volume":           ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-scaling":                        ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-search-quality-diagnosis":       ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-search-strategies":              ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-search-quality":                 ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),
    "qdrant-version-upgrade":                ("https://github.com/qdrant/skills", "qdrant/skills", "https://qdrant.tech", "Qdrant"),

    # ── OpenRouterTeam/skills ─────────────────────────────────────────────
    "openrouter-agent-migration":  ("https://github.com/OpenRouterTeam/skills", "OpenRouterTeam/skills", "https://openrouter.ai", "OpenRouter"),
    "openrouter-images":           ("https://github.com/OpenRouterTeam/skills", "OpenRouterTeam/skills", "https://openrouter.ai", "OpenRouter"),
    "openrouter-models":           ("https://github.com/OpenRouterTeam/skills", "OpenRouterTeam/skills", "https://openrouter.ai", "OpenRouter"),
    "openrouter-oauth":            ("https://github.com/OpenRouterTeam/skills", "OpenRouterTeam/skills", "https://openrouter.ai", "OpenRouter"),
    "openrouter-typescript-sdk":   ("https://github.com/OpenRouterTeam/skills", "OpenRouterTeam/skills", "https://openrouter.ai", "OpenRouter"),
    "create-agent-tui":            ("https://github.com/OpenRouterTeam/skills", "OpenRouterTeam/skills", "https://openrouter.ai", "OpenRouter"),
    "create-headless-agent":       ("https://github.com/OpenRouterTeam/skills", "OpenRouterTeam/skills", "https://openrouter.ai", "OpenRouter"),

    # ── streamlit/agent-skills ────────────────────────────────────────────
    "developing-with-streamlit":             ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "building-streamlit-chat-ui":            ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "building-streamlit-custom-components-v2":("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "building-streamlit-dashboards":         ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "building-streamlit-multipage-apps":     ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "choosing-streamlit-selection-widgets":  ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "connecting-streamlit-to-snowflake":     ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "creating-streamlit-themes":             ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "displaying-streamlit-data":             ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "improving-streamlit-design":            ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "optimizing-streamlit-performance":      ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "organizing-streamlit-code":             ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "setting-up-streamlit-environment":      ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "using-streamlit-cli":                   ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "using-streamlit-custom-components":     ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "using-streamlit-layouts":               ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "using-streamlit-markdown":              ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),
    "using-streamlit-session-state":         ("https://github.com/streamlit/agent-skills", "streamlit/agent-skills", "https://streamlit.io", "Streamlit"),

    # ── bmad-code-org/BMAD-METHOD ─────────────────────────────────────────
    "bmad-agent-analyst":           ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-agent-architect":         ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-agent-dev":               ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-agent-pm":                ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-agent-tech-writer":       ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-agent-ux-designer":       ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-check-implementation-readiness":("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-checkpoint-preview":      ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-code-review":             ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-correct-course":          ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-create-architecture":     ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-create-epics-and-stories":("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-create-prd":              ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-create-story":            ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-create-ux-design":        ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-dev-story":               ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-document-project":        ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-domain-research":         ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-edit-prd":                ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-generate-project-context":("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-market-research":         ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-prfaq":                   ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-product-brief":           ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-qa-generate-e2e-tests":   ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-quick-dev":               ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-retrospective":           ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-sprint-planning":         ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-sprint-status":           ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-technical-research":      ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),
    "bmad-validate-prd":            ("https://github.com/bmad-code-org/BMAD-METHOD", "bmad-code-org/BMAD-METHOD", "https://github.com/bmad-code-org", "BMAD Code Org"),

    # ── obra/superpowers (Jesse Vincent) ──────────────────────────────────
    # These are in engineering-craft/ and skills-management/
    "brainstorming":               ("https://github.com/obra/superpowers", "obra/superpowers", "https://github.com/obra", "Jesse Vincent"),
    "dispatching-parallel-agents": ("https://github.com/obra/superpowers", "obra/superpowers", "https://github.com/obra", "Jesse Vincent"),
    "executing-plans":             ("https://github.com/obra/superpowers", "obra/superpowers", "https://github.com/obra", "Jesse Vincent"),
    "subagent-driven-development": ("https://github.com/obra/superpowers", "obra/superpowers", "https://github.com/obra", "Jesse Vincent"),
    "writing-plans":               ("https://github.com/obra/superpowers", "obra/superpowers", "https://github.com/obra", "Jesse Vincent"),
    "writing-skills":              ("https://github.com/obra/superpowers", "obra/superpowers", "https://github.com/obra", "Jesse Vincent"),
    "find-skills":                 ("https://github.com/obra/superpowers", "obra/superpowers", "https://github.com/obra", "Jesse Vincent"),
    "systematic-debugging":        ("https://github.com/obra/superpowers", "obra/superpowers", "https://github.com/obra", "Jesse Vincent"),
    "using-git-worktrees":         ("https://github.com/obra/superpowers", "obra/superpowers", "https://github.com/obra", "Jesse Vincent"),
    "finishing-a-development-branch":("https://github.com/obra/superpowers", "obra/superpowers", "https://github.com/obra", "Jesse Vincent"),
    "requesting-code-review":      ("https://github.com/obra/superpowers", "obra/superpowers", "https://github.com/obra", "Jesse Vincent"),
    "receiving-code-review":       ("https://github.com/obra/superpowers", "obra/superpowers", "https://github.com/obra", "Jesse Vincent"),

    # ── github/awesome-copilot ────────────────────────────────────────────
    "react18-legacy-context":      ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "react18-lifecycle-patterns":  ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "react18-enzyme-to-rtl":       ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "react18-batching-patterns":   ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "react18-dep-compatibility":   ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "react18-string-refs":         ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "react-audit-grep-patterns":   ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "react19-concurrent-patterns": ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "react19-source-patterns":     ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "react19-test-patterns":       ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "gtm-0-to-1-launch":           ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "gtm-ai-gtm":                  ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "gtm-board-and-investor-communication":("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "gtm-developer-ecosystem":     ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "gtm-enterprise-account-planning":("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "gtm-enterprise-onboarding":   ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "gtm-operating-cadence":       ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "gtm-partnership-architecture":("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "gtm-positioning-strategy":    ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "gtm-product-led-growth":      ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "gtm-technical-product-pricing":("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "powerbi-modeling":            ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "suggest-awesome-github-copilot-skills":("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "suggest-awesome-github-copilot-instructions":("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "suggest-awesome-github-copilot-agents":("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "acreadiness-assess":          ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "acreadiness-generate-instructions":("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "acreadiness-policy":          ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "copilot-sdk":                 ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "copilot-instructions-blueprint-generator":("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "copilot-spaces":              ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "copilot-usage-metrics":       ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "copilot-cli-quickstart":      ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "agent-governance":            ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "ai-ready":                    ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "microsoft-skill-creator":     ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "vardoger-analyze":            ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),
    "workiq-copilot":              ("https://github.com/github/awesome-copilot", "github/awesome-copilot", "https://github.com/github", "GitHub Community"),

    # ── microsoft/skills ──────────────────────────────────────────────────
    "csharp-async":                ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "csharp-docs":                 ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "csharp-mstest":               ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "csharp-nunit":                ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "csharp-tunit":                ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "csharp-xunit":                ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "dotnet-best-practices":       ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "dotnet-design-pattern-review":("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "dotnet-timezone":             ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "dotnet-upgrade":              ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "mvvm-toolkit":                ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "mvvm-toolkit-di":             ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "mvvm-toolkit-messenger":      ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "nuget-manager":               ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "vscode-ext-commands":         ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "vscode-ext-localization":     ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "winapp-cli":                  ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "winmd-api-search":            ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "winui3-migration-guide":      ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "declarative-agents":          ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "entra-agent-user":            ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "foundry-agent-sync":          ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "hosted-agents":               ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "mcp-copilot-studio-server-generator":("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "mcp-create-adaptive-cards":   ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "mcp-create-declarative-agent":("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "mcp-deploy-manage-agents":    ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "microsoft-agent-framework":   ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "dataverse-python-advanced-patterns":("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "dataverse-python-production-code":  ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "dataverse-python-quickstart": ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "dataverse-python-usecase-builder":  ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "flowstudio-power-automate-build":   ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "flowstudio-power-automate-debug":   ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "flowstudio-power-automate-governance":("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "flowstudio-power-automate-mcp":     ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "flowstudio-power-automate-monitoring":("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "power-apps-code-app-scaffold":("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "power-bi-dax-optimization":   ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "power-bi-model-design-review":("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "power-bi-performance-troubleshooting":("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "power-bi-report-design-consultation":("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "power-platform-architect":    ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "power-platform-mcp-connector-suite":("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "aspnet-minimal-api-openapi":  ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "openapi-to-application-code": ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "typespec-api-operations":     ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "typespec-create-agent":       ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "typespec-create-api-plugin":  ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "ef-core":                     ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "aspire":                      ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "microsoft-code-reference":    ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "microsoft-docs":              ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "semantic-kernel":             ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),
    "fluentui-blazor":             ("https://github.com/microsoft/skills", "microsoft/skills", "https://microsoft.com", "Microsoft"),

    # ── microsoft/azure-skills ────────────────────────────────────────────
    "azure-deployment-preflight":  ("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),
    "azure-pricing":               ("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),
    "azure-static-web-apps":       ("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),
    "azure-resource-visualizer":   ("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),
    "azure-role-selector":         ("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),
    "azure-devops-cli":            ("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),
    "azure-smart-city-iot-solution-builder":("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),
    "azure-architecture-autopilot":("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),
    "azure-resource-health-diagnose":("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),
    "appinsights-instrumentation": ("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),
    "az-cost-optimize":            ("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),
    "update-avm-modules-in-bicep": ("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),
    "import-infrastructure-as-code":("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),
    "cloud-design-patterns":       ("https://github.com/microsoft/azure-skills", "microsoft/azure-skills", "https://azure.microsoft.com", "Microsoft Azure"),

    # ── microsoft/skills-for-fabric ───────────────────────────────────────
    "fabric-lakehouse":            ("https://github.com/microsoft/skills-for-fabric", "microsoft/skills-for-fabric", "https://microsoft.com", "Microsoft"),

    # ── muratcankoylan/Agent-Skills-for-Context-Engineering ───────────────
    "context-fundamentals":        ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "context-degradation":         ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "context-compression":         ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "context-optimization":        ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "latent-briefing":             ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "multi-agent-patterns":        ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "memory-systems":              ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "tool-design":                 ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "filesystem-context":          ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "bdi-mental-states":           ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "context-map":                 ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "mini-context-graph":          ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "what-context-needed":         ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "structured-autonomy-generate":("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "structured-autonomy-implement":("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
    "structured-autonomy-plan":    ("https://github.com/muratcankoylan/Agent-Skills-for-Context-Engineering", "muratcankoylan/Agent-Skills-for-Context-Engineering", "https://github.com/muratcankoylan", "Muratcan Koylan"),
}


def add_attribution(skill_dir: str, source_url: str, attribution_text: str,
                    creator_url: str, creator_name: str) -> bool:
    """Add source/attribution YAML fields and body blockquote to a SKILL.md file."""
    skill_path = os.path.join(skill_dir, "SKILL.md")
    if not os.path.exists(skill_path):
        print(f"  SKIP (no SKILL.md): {skill_dir}")
        return False

    with open(skill_path, "r", encoding="utf-8-sig") as f:
        content = f.read()

    # Skip if already has source attribution
    if "source:" in content:
        print(f"  SKIP (already attributed): {os.path.basename(skill_dir)}")
        return False

    # ── 1. Insert source + attribution after the last frontmatter field ──
    # Find the closing --- of frontmatter
    # Pattern: starts with ---, then content, then ---
    fm_match = re.match(r'^(---\n)(.*?\n)(---\n)', content, re.DOTALL)
    if not fm_match:
        print(f"  SKIP (no frontmatter): {skill_dir}")
        return False

    fm_open  = fm_match.group(1)
    fm_body  = fm_match.group(2)
    fm_close = fm_match.group(3)
    rest     = content[fm_match.end():]

    # Add source + attribution lines
    new_fm = (fm_open + fm_body
              + f'source: "{source_url}"\n'
              + f'attribution: "{attribution_text} by {creator_name}"\n'
              + fm_close)

    # ── 2. Add attribution blockquote at start of body ────────────────────
    blockquote = (f'\n> **Attribution:** Sourced from '
                  f'[{attribution_text}]({source_url}) by '
                  f'[{creator_name}]({creator_url}).\n')

    # Insert after first blank line in body, or at start of body
    # Find position right after frontmatter closing ---
    # If body already has a heading, insert before it; otherwise at top
    if rest.startswith('\n'):
        new_content = new_fm + blockquote + rest
    else:
        new_content = new_fm + blockquote + "\n" + rest

    with open(skill_path, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"  OK: {os.path.basename(skill_dir)} ← {attribution_text}")
    return True


def find_skill_dir(skill_name: str) -> str | None:
    """Walk skills/ to find a directory whose name matches skill_name."""
    for root, dirs, files in os.walk(BASE):
        for d in dirs:
            if d == skill_name:
                return os.path.join(root, d)
    return None


def main():
    group = sys.argv[1] if len(sys.argv) > 1 else "all"

    updated = 0
    skipped = 0

    for skill_name, (src_url, attr_text, creator_url, creator_name) in SOURCE_MAP.items():
        skill_dir = find_skill_dir(skill_name)
        if skill_dir is None:
            print(f"  NOT FOUND: {skill_name}")
            skipped += 1
            continue
        if add_attribution(skill_dir, src_url, attr_text, creator_url, creator_name):
            updated += 1
        else:
            skipped += 1

    print(f"\nDone. Updated: {updated}, Skipped/Not found: {skipped}")


if __name__ == "__main__":
    main()
