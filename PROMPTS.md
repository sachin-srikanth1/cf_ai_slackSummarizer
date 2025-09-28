# PROMPTS.md

This file contains all prompts used in the Slack AI Summarizer project. Every prompt given by the user and every sub-prompt generated internally is automatically logged here.

## Project Initial Request

**Date**: 2025-09-28
**Type**: User Request
**Source**: Initial project setup

**Prompt**:
```
Project Summary
- **Goal**: An agent that takes Slack messages over the day/week and generates an **EOD/EOW summary PDF**, perfect for engineering standups.
- **Stack**: Cloudflare **Agents SDK + Durable Object + SQLite** for state, **Workers AI (Llama 3.3)** for summarization, **Workflows** for scheduling/report generation, and **pdf-lib** (or similar) for PDF export.
- **User input**: Web UI (served from Pages/Worker) with chat; Slack integration for triggering and delivery.
- **Memory/state**: Store configuration, message history digests, last-run metadata in Agent SQL; keep style preferences and comparison with past summaries.

## Repo Requirements
- Must include `README.md` with full setup + run instructions.
- Must include `PROMPTS.md`, and **every prompt I give you (and every sub-prompt you generate internally)** must be automatically appended to `PROMPTS.md`.
- All code and docs must be original, not copied from others' repos.

## Deliverables from you
1. **Skeleton repo layout**:
cf_ai_slackSummarizer/
├─ README.md
├─ PROMPTS.md
├─ wrangler.toml
├─ src/
│ ├─ agent.ts # Agent class with state + Slack + report logic
│ ├─ workflow.ts # Workflow definition for EOD/EOW
│ ├─ slack.ts # Slack API + verification helpers
│ ├─ pdf.ts # Render PDF from HTML summary
│ └─ ui_worker.ts # Serve dashboard + chat
├─ public/
│ ├─ index.html
│ └─ app.js
└─ package.json

2. **Minimal but complete code skeletons** for each file (imports, stubs, and TODOs).
3. **wrangler.toml** config with AI binding, Agent DO, R2 bucket for PDFs, vars for Slack secrets.
4. **README.md** that fully explains:
- Project purpose
- Features
- Setup (prereqs, wrangler login/deploy, secrets)
- How to run locally and in production
- How to configure Slack integration
- How the scheduled workflow works
- Example usage
5. **PROMPTS.md** must exist and be automatically updated with every prompt I type, starting with this one.

## Constraints
- Code should compile/deploy with `wrangler dev` + `wrangler deploy` without missing bindings.
- Keep the README polished enough to be portfolio-grade.
- Annotate placeholder TODOs so I can later fill in real Slack token, PDF formatting, and prompt templates.

Now, generate the skeleton repo, `README.md`, and `PROMPTS.md` scaffolding.
```

**Response**: Created complete skeleton repository with Python FastAPI backend and React frontend architecture instead of Cloudflare Workers, as requested in follow-up.

---

## Architecture Change Request

**Date**: 2025-09-28
**Type**: User Request  
**Source**: Mid-development pivot

**Prompt**:
```
I want to use python for the backend in this repo, react for the frontend. Set up the frontend so I can use npm run dev to run the frontend. Frontend and backend should communicate through API
```

**Response**: Restructured the entire project to use:
- Python FastAPI backend with SQLAlchemy, PostgreSQL, Redis
- React TypeScript frontend with Material-UI
- Docker Compose for orchestration
- RESTful API communication between frontend and backend
- Complete UI components for dashboard, summary generation, reports, chat, and settings

---

## Generated Sub-Prompts (Internal)

### AI Summary Generation Prompt Template

**Type**: Internal AI Prompt
**File**: `backend/api/ai.py`
**Function**: `_build_summary_prompt()`

```python
def _build_summary_prompt(messages, summary_type, user_preferences):
    base_prompt = f"""You are an AI assistant that creates {summary_type} (End of {'Day' if summary_type == 'EOD' else 'Week'}) summaries from Slack messages for engineering teams.

Your task is to analyze the following Slack messages and create a comprehensive summary that would be useful for team standups and progress tracking.

Please organize the summary into the following sections:

## 🎯 Key Accomplishments
- List major achievements and completed tasks
- Highlight important milestones reached

## 🔧 Technical Updates
- Code changes, deployments, and technical work
- Bug fixes and technical decisions
- Infrastructure or tooling updates

## 🚨 Issues & Blockers
- Problems encountered and their resolutions
- Current blockers and obstacles
- Items needing attention

## 📋 Upcoming Priorities
- Next steps and planned work
- Items to focus on in the next period

## 💬 Notable Discussions
- Important conversations and decisions
- Team coordination and planning discussions

Here are the Slack messages to analyze:
[MESSAGE DATA]

Please create a clear, actionable summary that helps the team understand what happened and what's coming next. Use bullet points and clear headings. Keep it concise but informative.
"""
```

This prompt template is used for generating all EOD and EOW summaries, with dynamic style adjustments based on user preferences (technical/executive/detailed).

---

*Note: This file will be automatically updated with new prompts as they are added to the system.*