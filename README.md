# Slack AI Summarizer

An intelligent Slack bot that generates EOD/EOW summaries from team conversations using Cloudflare Workers AI.

## Summary

This tool automatically creates End of Day (EOD) and End of Week (EOW) reports by analyzing Slack messages. Simply mention the bot in any channel to generate structured summaries perfect for standups and progress tracking.

## Technical Overview

- **Backend**: Python FastAPI with MongoDB storage
- **AI**: Cloudflare Workers AI (Llama 3.3) for intelligent text analysis
- **Slack Integration**: Real-time webhook bot with @mention commands
- **Frontend**: Simple HTML dashboard for testing and management

## Example Usage

```
@cf_ai_slackSummarizer EOD

Bot Response:
📊 EOD Summary Generated

## Key Accomplishments
* Completed user authentication feature
* Fixed 3 critical bugs in payment system
* Deployed staging environment

## Technical Updates  
* Updated React to v18.2
* Implemented Redis caching

## Issues & Blockers
* AWS service outage affecting deployment

Processed 45 messages
PDF LINK -> _______
```

## Setup

1. **Clone and configure**:
```bash
git clone <repository-url>
cd cf_ai_slackSummarizer
cp .env.example .env
# Edit .env with your tokens
```

2. **Install and run backend**:
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. **Setup services**:
   - **Slack**: Create app at api.slack.com/apps, add OAuth scopes, get bot token
   - **Cloudflare**: Get Account ID and API token from dashboard
   - **MongoDB**: Install locally or use Atlas cloud
   - **ngrok**: `ngrok http 8000` for webhook URL

4. **Configure Slack webhooks**:
   - Add ngrok URL to Slack Event Subscriptions: `https://your-id.ngrok.io/api/slack/webhook`
   - Subscribe to `app_mention` and `message.channels` events

5. **Test**: `curl http://localhost:8000/health` should show all services healthy

## Commands

- `@bot EOD` - Generate end of day summary
- `@bot EOW` - Generate end of week summary  
- `@bot sync` - Sync recent messages
- `@bot help` - Show help