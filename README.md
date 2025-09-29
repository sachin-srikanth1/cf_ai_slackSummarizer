# 🤖 Slack AI Summarizer

An intelligent Slack bot that automatically generates EOD (End of Day) and EOW (End of Week) summaries from your team's Slack conversations using AI. Perfect for engineering standups, team communication, and keeping track of daily progress.

## ✨ Features

- **🤖 Slack Bot Integration**: Mention the bot directly in Slack channels to generate summaries
- **🧠 AI-Powered Summaries**: Uses Cloudflare Workers AI with Llama 3.3 for intelligent analysis
- **📊 Multiple Report Types**: End of Day (EOD) and End of Week (EOW) reports
- **📄 PDF Generation**: Professional PDF reports with formatted summaries
- **🔄 Real-time Message Sync**: Automatically syncs and stores Slack messages
- **🌐 Web Dashboard**: Simple HTML interface for testing and management
- **⚡ Quick Commands**: Easy-to-use bot commands via Slack mentions
- **🔍 Channel Filtering**: Works across all channels the bot has access to
- **📈 Message Analytics**: Shows processed message counts and timestamps

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- MongoDB (local or Atlas)
- Slack App with bot permissions
- Cloudflare Account with Workers AI access
- ngrok (for Slack webhook integration)

### 1. Clone & Setup Environment

```bash
git clone <repository-url>
cd cf_ai_slackSummarizer
cp .env.example .env
```

### 2. Configure Environment Variables

Edit `.env` with your credentials:

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# Cloudflare Workers AI Configuration
CLOUDFLARE_ACCOUNT_ID=your-cloudflare-account-id
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=slackSummarizer
```

### 3. Install Dependencies & Start Backend

```bash
# Install Python dependencies
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Start the backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Setup Slack App (Required for Bot Functionality)

#### Create Slack App:
1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Name: `cf_ai_slackSummarizer`
4. Select your workspace

#### Configure OAuth Scopes:
Go to **OAuth & Permissions** and add these Bot Token Scopes:
```
channels:read       - View basic information about public channels
channels:history    - View messages in public channels  
groups:read         - View basic information about private channels
groups:history      - View messages in private channels
chat:write          - Send messages as the bot
app_mentions:read   - View messages that mention the app
users:read          - View people in the workspace
```

#### Install App to Workspace:
1. Click "Install to Workspace"
2. Authorize the permissions
3. Copy the **Bot User OAuth Token** → Add to `.env` as `SLACK_BOT_TOKEN`
4. Go to **Basic Information** → Copy **Signing Secret** → Add to `.env` as `SLACK_SIGNING_SECRET`

### 5. Setup Cloudflare Workers AI

#### Get Cloudflare Credentials:
1. Sign up at [cloudflare.com](https://cloudflare.com)
2. Go to dashboard sidebar → Copy **Account ID**
3. Go to **My Profile** → **API Tokens** → **Create Token**
4. Use template: **Custom token** with permissions:
   - `Account:Cloudflare Workers:Edit`
   - `Zone:Zone:Read`
5. Copy token to `.env` as `CLOUDFLARE_API_TOKEN`

### 6. Setup MongoDB

#### Option A: Local MongoDB
```bash
# macOS
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb/brew/mongodb-community

# Ubuntu/Debian
sudo apt-get install mongodb-org
sudo systemctl start mongod
```

#### Option B: MongoDB Atlas (Cloud)
1. Sign up at [mongodb.com/atlas](https://mongodb.com/atlas)
2. Create free cluster
3. Get connection string → Update `MONGODB_URL` in `.env`

### 7. Enable Slack Webhooks (For @mentions)

#### Setup ngrok:
```bash
# Install ngrok
brew install ngrok  # or download from ngrok.com

# Expose your backend
ngrok http 8000
```

#### Configure Slack Event Subscriptions:
1. Copy the ngrok HTTPS URL (e.g., `https://abc123.ngrok.io`)
2. In your Slack app → **Event Subscriptions**
3. Enable Events → **Request URL**: `https://abc123.ngrok.io/api/slack/webhook`
4. **Subscribe to bot events**:
   - `app_mention` - When someone mentions your bot
   - `message.channels` - To read channel messages
5. **Save Changes** → **Reinstall App to Workspace**

### 8. Test the Setup

#### Check Backend Health:
```bash
curl http://localhost:8000/health
```

Should return all services as "healthy".

#### Start Web Interface:
```bash
# In the frontend directory
python3 -m http.server 8080
```

Visit: http://localhost:8080

## 🎯 Using the Slack Bot

### Add Bot to Channels
1. Go to any Slack channel
2. Type: `/invite @cf_ai_slackSummarizer`
3. The bot is now ready to use in that channel

### Bot Commands

Mention the bot with these commands:

```bash
@cf_ai_slackSummarizer EOD          # Generate End of Day summary
@cf_ai_slackSummarizer EOW          # Generate End of Week summary  
@cf_ai_slackSummarizer sync         # Sync recent messages
@cf_ai_slackSummarizer help         # Show help message
```

### Example Usage:

```
You: @cf_ai_slackSummarizer EOD

Bot: 🔄 Generating EOD summary... This may take a moment.
     📈 Processing 45 messages from 2025-09-29...
     📊 EOD Summary Generated
     
     ## 🎯 Key Accomplishments
     * Completed user authentication feature
     * Fixed 3 critical bugs in payment system
     * Deployed staging environment
     
     ## 🔧 Technical Updates  
     * Updated React to v18.2
     * Implemented Redis caching
     * Database migration completed
     
     ## 🚨 Issues & Blockers
     * AWS service outage affecting deployment
     * Waiting for API keys from third-party service
     
     ## 📋 Upcoming Priorities
     * Performance optimization sprint
     * Security audit preparation
     
     📈 Processed 45 messages
```

## 🌐 Web Dashboard

Access the web interface at http://localhost:8080

### Features:
- **📊 System Status**: Real-time health monitoring
- **⚡ Quick Actions**: One-click summary generation
- **📺 Channel Management**: View available Slack channels
- **📝 Custom Summaries**: Generate reports with custom date ranges
- **🎛️ Advanced Options**: Custom AI prompts and channel filtering

### Quick Actions:
- **🔄 Sync Messages**: Pull latest messages from Slack
- **📊 Today's EOD**: Generate end-of-day summary for today
- **📈 This Week EOW**: Generate week summary
- **🧪 Test API**: Verify backend connectivity

## 🔧 API Reference

The backend provides a REST API at `http://localhost:8000`:

### Health Check
```bash
GET /health
```

### Generate Summary
```bash
POST /api/summary/generate
Content-Type: application/json

{
  "type": "EOD",
  "date_range": {
    "start": "2025-09-29T00:00:00Z",
    "end": "2025-09-29T23:59:59Z"
  }
}
```

### Sync Slack Messages
```bash
POST /api/slack/sync
Content-Type: application/json

{
  "hours_back": 24
}
```

### Get Slack Channels
```bash
GET /api/slack/channels
```

### Chat with AI
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "Generate EOD summary"
}
```

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Slack App     │◄───┤   ngrok Tunnel   │◄───┤  Backend API    │
│   (Webhooks)    │    │   (Dev only)     │    │  (FastAPI)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Web Dashboard  │───►│   Backend API    │◄───┤    MongoDB      │
│   (HTML/JS)     │    │   (Port 8000)    │    │   (Database)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                 │
                                 ▼
                       ┌─────────────────┐
                       │ Cloudflare AI   │
                       │  (Llama 3.3)    │
                       └─────────────────┘
```

### Components:
- **Backend**: Python FastAPI server handling API requests
- **Database**: MongoDB for storing messages and summaries
- **AI Service**: Cloudflare Workers AI with Llama 3.3
- **Slack Integration**: Webhook-based bot for real-time interaction
- **Web Interface**: Simple HTML dashboard for management
- **Development Tunnel**: ngrok for local webhook testing

## 🛠️ Development

### Backend Development
```bash
cd backend
source venv/bin/activate

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Format code
black .
isort .

# Install new dependencies
pip install package_name
pip freeze > requirements.txt
```

### Frontend Development
```bash
cd frontend

# Serve locally
python3 -m http.server 8080

# Or with Node.js
npx serve . -p 8080
```

### Testing
```bash
# Test backend health
curl http://localhost:8000/health

# Test webhook locally
python3 test_webhook.py

# Test bot functionality
python3 trigger_bot.py
```

## 🚨 Troubleshooting

### Bot Not Responding in Slack
1. **Check ngrok**: Ensure tunnel is running and URL is configured
2. **Verify Permissions**: Bot needs proper OAuth scopes
3. **Check Logs**: Look at backend logs for webhook errors
4. **Reinstall App**: After permission changes, reinstall to workspace

### Backend Issues
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check for port conflicts
lsof -i :8000

# Restart backend
pkill -f uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Database Issues
```bash
# Check MongoDB status
brew services list | grep mongodb  # macOS
sudo systemctl status mongod       # Linux

# Test connection
mongosh mongodb://localhost:27017
```

### AI Service Issues
- Verify Cloudflare Account ID and API Token
- Check Cloudflare dashboard for usage limits
- Ensure API token has Workers AI permissions

### Common Error Messages

**"Error connecting to backend"**
- Backend not running on port 8000
- CORS issues (check browser console)

**"Slack API failed"**
- Invalid bot token or signing secret
- Bot not added to channel
- Missing OAuth permissions

**"AI Service unhealthy"**
- Invalid Cloudflare credentials
- API quota exceeded
- Network connectivity issues

## 🔒 Security Notes

- **Environment Variables**: Never commit `.env` files
- **Slack Secrets**: Keep bot tokens and signing secrets secure
- **API Keys**: Protect Cloudflare API tokens
- **Production**: Use proper secret management for deployment
- **Webhooks**: In production, use HTTPS and verify signatures

## 📈 Production Deployment

For production deployment:

1. **Use MongoDB Atlas** instead of local MongoDB
2. **Configure proper HTTPS** instead of ngrok
3. **Set up proper logging** and monitoring
4. **Use environment variables** for all secrets
5. **Implement rate limiting** for API endpoints
6. **Monitor Cloudflare usage** and costs

## 📝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request