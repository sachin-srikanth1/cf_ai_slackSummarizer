# Slack AI Summarizer

An intelligent agent that automatically generates EOD (End of Day) and EOW (End of Week) summary PDFs from Slack messages, perfect for engineering standups and team communication.

## 🚀 Features

- **AI-Powered Summaries**: Generate intelligent summaries using Cloudflare Workers AI with Llama 3.3
- **Multiple Report Types**: End of Day (EOD) and End of Week (EOW) reports
- **PDF Export**: Professional PDF reports with customizable formatting
- **Slack Integration**: Direct integration with Slack for message collection and delivery
- **Web Dashboard**: React-based frontend for configuration and report management
- **Chat Interface**: Interactive AI assistant for natural language commands
- **Scheduled Reports**: Automated report generation with configurable timing
- **Channel Filtering**: Include/exclude specific channels from summaries
- **Custom Prompts**: Personalize AI summary generation with custom instructions
- **Report History**: Track and download previous reports

## 🏗️ Architecture

- **Backend**: Python FastAPI with MongoDB/Beanie ODM
- **Frontend**: React with TypeScript and Material-UI
- **Database**: MongoDB for flexible data persistence
- **AI Provider**: Cloudflare Workers AI with Llama 3.3 for powerful summarization
- **State Management**: Cloudflare Durable Objects pattern for persistent state
- **Workflows**: Cloudflare Workflows pattern for coordinated task execution
- **PDF Generation**: ReportLab for professional PDF creation
- **Local Development**: Simple setup with virtual environments

## 📋 Prerequisites

- Node.js 18+
- Python 3.11+
- MongoDB (local or cloud)
- Slack App with bot token and signing secret
- Cloudflare Account with Workers AI access
- Cloudflare API Token with AI permissions

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone <repository-url>
cd cf_ai_slackSummarizer
```

### 2. Environment Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here

# Cloudflare Workers AI Configuration (Llama 3.3)
CLOUDFLARE_ACCOUNT_ID=your-cloudflare-account-id-here
CLOUDFLARE_API_TOKEN=your-cloudflare-api-token-here

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=slack_summarizer

# Other settings...
```

### 3. Cloudflare Workers AI Setup

1. **Create Cloudflare Account**: Sign up at [cloudflare.com](https://www.cloudflare.com/)
2. **Enable Workers AI**: Go to your dashboard and enable Workers AI
3. **Get Account ID**: 
   - Go to the right sidebar of your Cloudflare dashboard
   - Copy your Account ID
4. **Create API Token**:
   - Go to "My Profile" → "API Tokens"
   - Create a custom token with permissions:
     - `Account:Cloudflare Workers:Edit`
     - `Zone:Zone:Read` (if using custom domains)
   - Copy the token to `CLOUDFLARE_API_TOKEN`
5. **Configure Environment**: Add your Account ID and API Token to `.env`

The system uses Llama 3.3 (`@cf/meta/llama-3.3-70b-instruct-fp8`) for all AI operations including:
- Slack message summarization
- Chat interactions
- Custom summary generation
- Summary improvement suggestions

### 4. Slack App Setup

1. Create a new Slack app at [api.slack.com](https://api.slack.com/apps)
2. Enable the following OAuth scopes:
   - `channels:read` - View basic information about public channels
   - `channels:history` - View messages in public channels
   - `groups:read` - View basic information about private channels
   - `groups:history` - View messages in private channels
   - `chat:write` - Send messages
   - `files:write` - Upload files
   - `users:read` - View people in the workspace

3. Install the app to your workspace
4. Copy the Bot User OAuth Token to `SLACK_BOT_TOKEN`
5. Copy the Signing Secret to `SLACK_SIGNING_SECRET`

### 5. Install MongoDB

#### Option 1: Local MongoDB Installation

**macOS (using Homebrew):**
```bash
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb/brew/mongodb-community
```

**Ubuntu/Debian:**
```bash
sudo apt-get install gnupg curl
curl -fsSL https://www.mongodb.org/static/pgp/server-7.0.asc | sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg --dearmor
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
```

**Windows:**
Download and install from https://www.mongodb.com/try/download/community

#### Option 2: MongoDB Atlas (Cloud)

1. Sign up at https://www.mongodb.com/atlas
2. Create a free cluster
3. Get your connection string
4. Update `MONGODB_URL` in `.env` with your Atlas connection string

### 6. Install Dependencies

```bash
# Install root dependencies (includes concurrently for running both servers)
npm install

# Install all dependencies for both frontend and backend
npm run setup
```

### 7. Running the Application

#### Option 1: Start Both Services Together (Recommended)

```bash
npm start
```

This will start both the frontend (http://localhost:3000) and backend (http://localhost:8000) simultaneously.

#### Option 2: Start Services Separately

```bash
# Terminal 1 - Start backend
npm run start-backend

# Terminal 2 - Start frontend  
npm run dev
```

#### For Windows Users

If you're on Windows, use the Windows-specific backend script:

```bash
npm run start-backend-windows
```

### 8. Verify Setup

1. **MongoDB**: Ensure MongoDB is running (local) or Atlas connection works
2. **Cloudflare Workers AI**: Verify credentials are correct and AI service is accessible
3. **Frontend**: Should be available at http://localhost:3000
4. **Backend API**: Should be available at http://localhost:8000
5. **Health Check**: http://localhost:8000/health should show all services as healthy
6. **AI Service**: The health check should confirm Cloudflare Workers AI connectivity

## 🌐 Usage

### Web Dashboard

1. Open your browser to `http://localhost:3000`
2. Navigate through the interface:
   - **Dashboard**: Overview and quick actions
   - **Generate**: Create new EOD/EOW reports
   - **Reports**: View and download previous reports
   - **Chat**: Interact with the AI assistant
   - **Settings**: Configure preferences and scheduling

### API Endpoints

The backend API is available at `http://localhost:8000` with the following key endpoints:

- `GET /health` - Health check
- `POST /api/summary/generate` - Generate new summary
- `GET /api/reports` - List all reports
- `GET /api/slack/channels` - Get Slack channels
- `POST /api/chat` - Chat with AI assistant
- `GET /api/preferences` - Get user preferences
- `PUT /api/preferences` - Update preferences

### Slack Integration

The app automatically syncs messages from your Slack workspace. You can:

1. **Manual Sync**: Use the "Sync Messages" button in the dashboard
2. **Automatic Sync**: Configure background sync in settings
3. **Channel Selection**: Choose specific channels to include/exclude

### Report Generation

#### Generate EOD Report:
```bash
curl -X POST http://localhost:8000/api/summary/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "type": "EOD",
    "date_range": {
      "start": "2024-01-15T00:00:00Z",
      "end": "2024-01-15T23:59:59Z"
    }
  }'
```

#### Generate EOW Report:
```bash
curl -X POST http://localhost:8000/api/summary/generate \\
  -H "Content-Type: application/json" \\
  -d '{
    "type": "EOW",
    "date_range": {
      "start": "2024-01-15T00:00:00Z",
      "end": "2024-01-21T23:59:59Z"
    }
  }'
```

## ⚙️ Configuration

### Summary Styles

- **Technical**: Focus on code changes, bugs, and implementation details
- **Executive**: High-level progress, milestones, and business impact  
- **Detailed**: Comprehensive coverage with full context

### Scheduling

Configure automatic report generation:

- **EOD Reports**: Daily at specified time (e.g., 5:00 PM)
- **EOW Reports**: Weekly on specified day and time (e.g., Friday 5:00 PM)

### Channel Filtering

- Include specific channels for focused reports
- Exclude noisy channels from summaries
- Support for both public and private channels

## 🚀 Production Deployment

For production deployment, consider:

### Environment Variables

Set the following environment variables for production:

```env
ENVIRONMENT=production
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/slack_summarizer  # Use MongoDB Atlas for production
SLACK_BOT_TOKEN=xoxb-production-token
CLOUDFLARE_ACCOUNT_ID=your-production-account-id
CLOUDFLARE_API_TOKEN=your-production-api-token
```

### Security Considerations

- Use MongoDB Atlas for production instead of local MongoDB
- Store API keys and Cloudflare tokens in secure secret management
- Enable HTTPS with reverse proxy (nginx, Cloudflare)
- Configure CORS properly for your domain
- Implement rate limiting (Cloudflare Workers AI has built-in limits)
- Regular security updates
- Monitor Cloudflare Workers AI usage and costs

## 📊 Monitoring

### Health Checks

- Backend: `GET /health`
- Database connectivity check
- Cloudflare Workers AI availability
- State management system status
- Workflow coordination health

### Logs

View application logs:
```bash
# Backend logs
cd backend && source venv/bin/activate && python -m uvicorn main:app --log-level info

# Check backend processes
ps aux | grep uvicorn
```

## 🔧 Development

### Backend Development

```bash
# Activate virtual environment
cd backend && source venv/bin/activate

# Run tests
npm run test-backend

# Format code
npm run format-backend

# Or manually:
black .
isort .
```

### Frontend Development

```bash
cd frontend
# Install dependencies
npm install

# Run development server
npm start

# Run tests
npm test

# Build for production
npm run build
```

### Adding New Features

1. Backend: Add new endpoints in `main.py`
2. Frontend: Create new components in `src/components`
3. Database: Update MongoDB models in `models/database.py` (using Beanie)
4. Update API service in `frontend/src/services/apiService.ts`

## 🐛 Troubleshooting

### Common Issues

**Backend won't start:**
- Check if Python virtual environment is activated
- Verify all required environment variables are set in `.env`
- Make sure you're in the correct directory when running commands

**Python dependencies issues:**
```bash
# Recreate virtual environment
cd backend
rm -rf venv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

**Frontend dependencies issues:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Slack integration not working:**
- Verify bot token and signing secret in `.env`
- Check Slack app permissions
- Ensure bot is added to channels

**Frontend can't connect to backend:**
- Check backend is running: `curl http://localhost:8000/health`
- Verify backend is running on port 8000
- Check CORS configuration in `backend/main.py`

**MongoDB connection issues:**
```bash
# Check if MongoDB is running locally
brew services list | grep mongodb  # macOS
sudo systemctl status mongod       # Linux

# Test connection
mongosh  # Should connect to local MongoDB
```

**AI summaries failing:**
- Verify Cloudflare Account ID and API Token in `.env`
- Check Cloudflare Workers AI usage limits and account status
- Ensure API token has correct permissions (Workers AI access)
- Verify internet connection for Cloudflare API calls
- Check Cloudflare status page for service availability

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Create an issue on GitHub with details

---

**Generated with AI assistance for rapid prototyping and development.**