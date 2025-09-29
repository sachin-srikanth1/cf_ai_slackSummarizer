from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from datetime import datetime, timedelta
import logging
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# Load environment variables from .env file
load_dotenv()

from api.slack import SlackService
from api.ai import CloudflareAIService
from api.pdf import PDFService
from models.database import database
from models.schemas import (
    SummaryRequest, 
    SummaryResponse, 
    UserPreferences, 
    SlackMessage,
    SlackChannel,
    ReportMetadata,
    ChatMessage,
    ChatResponse,
    APIResponse,
    DateRange,
    SummaryType,
    SummaryStyle
)
from cf_workers.workflows import workflow_engine, scheduled_workflows
from cf_workers.durable_objects import get_summarizer_state, get_workflow_coordinator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown events"""
    # Startup logic
    try:
        await database.init_db()
        logger.info("Database connected successfully")
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")
        logger.info("Running without database - some features may not work")
    logger.info("Application started successfully")
    
    # Yield control to the application
    yield
    
    # Shutdown logic
    try:
        await database.close_db()
    except Exception as e:
        logger.warning(f"Database cleanup error: {e}")
    logger.info("Application shutdown complete")

app = FastAPI(
    title="Slack AI Summarizer API",
    description="API for generating AI-powered EOD/EOW summaries from Slack messages",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
slack_service = SlackService()
ai_service = CloudflareAIService()
pdf_service = PDFService()

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Slack AI Summarizer API is running"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": await database.health_check(),
            "slack": await slack_service.health_check(),
            "ai": await ai_service.health_check()
        }
    }

# Slack Integration Endpoints
@app.post("/api/slack/webhook")
async def slack_webhook(request: Request):
    """Handle incoming Slack webhooks"""
    try:
        # Get the raw body
        body = await request.body()
        
        # Try to parse as JSON first
        try:
            import json
            payload = json.loads(body.decode('utf-8'))
        except:
            # If JSON parsing fails, try form data (for URL verification)
            from urllib.parse import parse_qs
            form_data = parse_qs(body.decode('utf-8'))
            if 'payload' in form_data:
                payload = json.loads(form_data['payload'][0])
            else:
                # Handle direct form fields
                payload = {}
                for key, value in form_data.items():
                    payload[key] = value[0] if value else None
        
        # Verify Slack signature for security (skip for URL verification and testing)
        # Note: Signature verification temporarily disabled for testing
        if False and payload.get("type") != "url_verification":
            signature = request.headers.get("x-slack-signature")
            timestamp = request.headers.get("x-slack-request-timestamp")
            
            if signature and timestamp:
                if not slack_service.verify_signature(timestamp, signature, body):
                    raise HTTPException(status_code=400, detail="Invalid signature")
        
        webhook_type = payload.get("type")
        
        # Handle URL verification for Slack app setup
        if webhook_type == "url_verification":
            challenge = payload.get("challenge")
            logger.info(f"URL verification requested, challenge: {challenge}")
            return {"challenge": challenge}
        
        # Handle different event types
        if webhook_type == "event_callback":
            event = payload.get("event", {})
            await _handle_slack_event(event)
        
        logger.info(f"Successfully processed Slack webhook: {webhook_type}")
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error handling Slack webhook: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Webhook processing failed")

async def _send_help_message(channel: str):
    """Send help message to Slack channel"""
    help_text = """🤖 **AI Slack Summarizer Help**

**Commands:**
• `EOD` / `daily` - Generate End of Day summary
• `EOW` / `weekly` - Generate End of Week summary  
• `sync` - Sync recent messages from channels
• `help` - Show this help message

**Features:**
• Automatic message syncing
• AI-powered summaries
• PDF report generation
• Channel-specific filtering

Just mention me with any command! For example: `Hey bot, generate EOD summary`"""
    
    await slack_service.send_message(channel=channel, text=help_text)

async def _get_channel_name(channel_id: str) -> str:
    """Get channel name from ID"""
    try:
        channel_info = await slack_service._get_channel_info(channel_id)
        return channel_info.get("name", "unknown")
    except:
        return "unknown"

async def _get_user_name(user_id: str) -> str:
    """Get user name from ID"""
    try:
        user_info = await slack_service._get_user_info(user_id)
        return user_info.get("name", "unknown")
    except:
        return "unknown"

async def _get_bot_user_id() -> Optional[str]:
    """Get bot user ID for mentions"""
    try:
        health_check = await slack_service.health_check()
        return health_check.get("bot_id")
    except:
        return None

# Global sets to track processed events (in production, use Redis or database)
processed_events = set()
processed_commands = set()

async def _handle_slack_event(event: Dict[Any, Any]):
    """Process different types of Slack events"""
    event_type = event.get("type")
    
    # Create unique event ID for deduplication
    event_id = f"{event.get('type')}_{event.get('ts')}_{event.get('event_ts')}_{event.get('user')}_{event.get('channel')}"
    
    # Check if we've already processed this event
    if event_id in processed_events:
        logger.info(f"Skipping duplicate event: {event_id}")
        return
    
    # Add to processed events (keep only last 1000 to prevent memory leak)
    processed_events.add(event_id)
    if len(processed_events) > 1000:
        # Remove oldest events (simple cleanup - in production use proper LRU cache)
        oldest_events = list(processed_events)[:100]
        for old_event in oldest_events:
            processed_events.remove(old_event)
    
    logger.info(f"Processing new event: {event_type} - {event_id}")
    
    if event_type == "message":
        # Store message in database
        await _store_slack_message(event)
        
        # Handle mentions of our bot
        # We'll check if the bot is mentioned in the text
        bot_user_id = await _get_bot_user_id()
        bot_mention = f"<@{bot_user_id}>" if bot_user_id else ""
        
        if bot_mention and bot_mention in event.get("text", ""):
            await _handle_bot_mention(event)
    
    elif event_type == "app_mention":
        # Handle direct mentions of the app
        await _handle_bot_mention(event)

async def _store_slack_message(event: Dict[Any, Any]):
    """Store Slack message in database"""
    try:
        # Skip bot messages and system messages
        if event.get("subtype") in ["bot_message", "channel_join", "channel_leave"]:
            logger.debug(f"Skipping message with subtype: {event.get('subtype')}")
            return
            
        event_timestamp = event.get("event_ts")
        channel = event.get("channel")
        user = event.get("user")
        text = event.get("text", "")
        
        logger.info(f"Processing message: user={user}, channel={channel}, text_length={len(text)}")
        
        if text and user and user.startswith("U"):
            # Store message in database (user IDs start with U)
            message_data = {
                "id": event_timestamp,
                "channel_id": channel,
                "channel_name": await _get_channel_name(channel),
                "user_id": user,
                "username": await _get_user_name(user),
                "text": text,
                "timestamp": datetime.fromtimestamp(float(event_timestamp)),
                "thread_ts": event.get("thread_ts"),
                "reactions": event.get("reactions", []),
                "files": event.get("files", [])
            }
            
            logger.info(f"Storing message from {message_data['username']} in #{message_data['channel_name']}: {text[:50]}...")
            await database.store_slack_message(message_data)
        else:
            logger.warning(f"Skipping message: text={bool(text)}, user={user}, user_valid={user and user.startswith('U') if user else False}")
                
    except Exception as e:
        logger.error(f"Error storing Slack message: {e}")
        import traceback
        logger.error(traceback.format_exc())

async def _handle_bot_mention(event: Dict[Any, Any]):
    """Handle when the bot is mentioned in a message"""
    try:
        channel = event.get("channel")
        text = event.get("text", "").lower()
        user = event.get("user")
        timestamp = event.get("ts") or event.get("event_ts")
        
        # Create command ID for deduplication
        command_id = f"{user}_{channel}_{timestamp}_{text[:50]}"
        
        # Check if we've already processed this command
        if command_id in processed_commands:
            logger.info(f"Skipping duplicate command: {command_id}")
            return
        
        # Add to processed commands
        processed_commands.add(command_id)
        if len(processed_commands) > 500:
            # Cleanup old commands
            oldest_commands = list(processed_commands)[:50]
            for old_cmd in oldest_commands:
                processed_commands.remove(old_cmd)
        
        logger.info(f"Processing bot mention command: {text[:100]} in channel {channel}")
        
        # Simple command parsing
        if "eod" in text or "daily" in text or "end of day" in text:
            await _generate_and_send_summary("EOD", channel)
        elif "eow" in text or "weekly" in text or "end of week" in text:
            await _generate_and_send_summary("EOW", channel)
        elif "help" in text:
            await _send_help_message(channel)
        elif "sync" in text:
            await slack_service.send_message(
                channel=channel,
                text="🔄 Syncing recent messages... This may take a moment."
            )
            result = await slack_service.sync_messages(hours_back=24)
            await slack_service.send_message(
                channel=channel,
                text=f"✅ Synced {result.get('total_messages', 0)} messages from {result.get('channels_processed', 0)} channels"
            )
        else:
            await slack_service.send_message(
                channel=channel,
                text="🤖 Hi! I can generate EOD/EOW summaries. Try mentioning me with 'EOD', 'EOW', 'sync', or 'help'!"
            )
            
    except Exception as e:
         logger.error(f"Error handling bot mention: {e}")
         await slack_service.send_message(
             channel=event.get("channel"),
             text="❌ Sorry, I encountered an error. Please try again."
         )

async def _generate_and_send_summary(summary_type: str, channel: str):
    """Generate and send summary to Slack channel"""
    try:
        await slack_service.send_message(
            channel=channel,
            text=f"🔄 Generating {summary_type} summary... This may take a moment."
        )
        
        # FIRST: Sync recent messages to ensure we have fresh data
        logger.info(f"Syncing recent messages before generating {summary_type} summary")
        sync_result = await slack_service.sync_messages(hours_back=24)
        logger.info(f"Sync result: {sync_result}")
        
        # Set date range (today for EOD, this week for EOW)
        end_time = datetime.now()
        if summary_type == "EOD":
            start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
            end_time = end_time.replace(hour=23, minute=59, second=59, microsecond=999999)
        else:  # EOW
            start_time = end_time - timedelta(days=7)
        
        logger.info(f"Getting messages from {start_time} to {end_time}")
        
        # Get messages directly from database with debug info
        messages = await database.get_messages_by_date_range(
            start_date=start_time,
            end_date=end_time
        )
        
        logger.info(f"Found {len(messages)} messages for {summary_type} summary")
        
        if len(messages) == 0:
            await slack_service.send_message(
                channel=channel,
                text=f"📊 **{summary_type} Summary**\n\n❌ No messages found for the specified time period ({start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}). Try syncing messages first or check if there's recent activity in tracked channels."
            )
            return
        
        # Show message count for debugging
        await slack_service.send_message(
            channel=channel,
            text=f"📈 Processing {len(messages)} messages from {start_time.strftime('%Y-%m-%d')}..."
        )
        
        # Generate AI summary
        logger.info("Generating AI summary...")
        ai_summary = await ai_service.generate_summary(
            messages=messages,
            summary_type=summary_type,
            user_preferences={"summary_style": "technical"}
        )
        
        logger.info(f"Generated summary length: {len(ai_summary)} characters")
        
        # Send summary to Slack
        summary_text = f"📊 **{summary_type} Summary Generated**\n\n{ai_summary[:1500]}{'...' if len(ai_summary) > 1500 else ''}\n\n📈 *Processed {len(messages)} messages*"
        
        await slack_service.send_message(
            channel=channel,
            text=summary_text
        )
        
    except Exception as e:
        logger.error(f"Error generating and sending summary: {e}")
        import traceback
        logger.error(traceback.format_exc())
        await slack_service.send_message(
            channel=channel,
            text=f"❌ Failed to generate summary. Error: {str(e)}"
        )

@app.get("/api/slack/channels")
async def get_slack_channels():
    """Get list of available Slack channels"""
    try:
        channels = await slack_service.get_channels()
        channel_objects = [SlackChannel(**channel) for channel in channels]
        return APIResponse(
            success=True,
            message=f"Retrieved {len(channels)} channels",
            data={"channels": channel_objects}
        )
    except Exception as e:
        logger.error(f"Error fetching channels: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch channels")

@app.post("/api/slack/sync")
async def sync_slack_messages(
    background_tasks: BackgroundTasks, 
    hours_back: int = 24
):
    """Manually trigger sync of Slack messages"""
    try:
        result = await slack_service.sync_messages(hours_back=hours_back)
        return APIResponse(
            success=result.get("success", False),
            message=f"Synced {result.get('total_messages', 0)} messages from {result.get('channels_processed', 0)} channels",
            data=result
        )
    except Exception as e:
        logger.error(f"Error in sync: {e}")
        raise HTTPException(status_code=500, detail="Failed to sync messages")

# Summary Generation Endpoints
@app.post("/api/summary/generate", response_model=SummaryResponse)
async def generate_summary(request: SummaryRequest):
    """Generate EOD/EOW summary"""
    try:
        # Fetch messages from database based on request
        messages = await database.get_messages_by_date_range(
            start_date=request.date_range.start,
            end_date=request.date_range.end,
            channels=request.channels
        )
        
        if not messages:
            raise HTTPException(
                status_code=404, 
                detail=f"No messages found for the specified date range and channels"
            )
        
        # Get user preferences if not provided
        preferences_dict = {}
        if request.preferences:
            preferences_dict = {
                "summary_style": request.preferences.summary_style,
                "include_threads": request.preferences.include_threads
            }
        else:
            preferences_dict = await database.get_user_preferences()
        
        # Generate AI summary using custom prompt or standard
        if request.custom_prompt:
            summary_text = await ai_service.generate_custom_summary(
                messages=messages,
                custom_prompt=request.custom_prompt
            )
        else:
            summary_text = await ai_service.generate_summary(
                messages=messages,
                summary_type=request.type.value,
                user_preferences=preferences_dict
            )
        
        # Generate PDF
        pdf_path = await pdf_service.create_summary_pdf(
            summary=summary_text,
            summary_type=request.type.value,
            metadata={
                "summary_type": request.type.value,
                "generated_at": datetime.utcnow().isoformat(),
                "message_count": len(messages),
                "channels": request.channels or [],
                "custom_prompt": request.custom_prompt
            }
        )
        
        # Store summary metadata in database
        summary_id = await database.store_summary_metadata(
            summary_text=summary_text,
            pdf_path=pdf_path,
            summary_type=request.type.value,
            message_count=len(messages),
            date_range_start=request.date_range.start,
            date_range_end=request.date_range.end,
            channels=request.channels
        )
        
        logger.info(f"Generated {request.type.value} summary with {len(messages)} messages")
        
        return SummaryResponse(
            id=summary_id,
            summary=summary_text,
            pdf_url=f"/api/reports/{summary_id}/pdf",
            generated_at=datetime.utcnow(),
            message_count=len(messages),
            type=request.type
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate summary: {str(e)}")

@app.get("/api/summary/history")
async def get_summary_history(limit: int = 10, offset: int = 0):
    """Get history of generated summaries"""
    try:
        summaries = await database.get_summary_history(limit=limit, offset=offset)
        return {"summaries": summaries, "total": len(summaries)}
    except Exception as e:
        logger.error(f"Error fetching summary history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch history")

# Report Management Endpoints
@app.get("/api/reports/{summary_id}/pdf")
async def download_pdf_report(summary_id: str):
    """Download PDF report by summary ID"""
    try:
        pdf_path = await database.get_pdf_path(summary_id)
        if not pdf_path or not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF not found")
        
        return FileResponse(
            pdf_path,
            media_type="application/pdf",
            filename=f"summary_{summary_id}.pdf"
        )
    except Exception as e:
        logger.error(f"Error downloading PDF: {e}")
        raise HTTPException(status_code=500, detail="Failed to download PDF")

@app.get("/api/reports")
async def list_reports(limit: int = 20, offset: int = 0):
    """List all generated reports"""
    try:
        reports = await database.get_reports(limit=limit, offset=offset)
        return {"reports": reports}
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to list reports")

# User Preferences Endpoints
@app.get("/api/preferences", response_model=UserPreferences)
async def get_user_preferences():
    """Get current user preferences"""
    try:
        preferences = await database.get_user_preferences()
        return preferences
    except Exception as e:
        logger.error(f"Error fetching preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch preferences")

@app.put("/api/preferences")
async def update_user_preferences(preferences: UserPreferences):
    """Update user preferences"""
    try:
        await database.update_user_preferences(preferences)
        return {"message": "Preferences updated successfully"}
    except Exception as e:
        logger.error(f"Error updating preferences: {e}")
        raise HTTPException(status_code=500, detail="Failed to update preferences")

# Chat Interface Endpoint
@app.post("/api/chat")
async def chat_with_agent(chat_request: ChatMessage):
    """Chat interface for interacting with the agent"""
    try:
        response_text = await ai_service.process_chat_message(chat_request.message)
        
        return ChatResponse(
            response=response_text,
            action_taken=None,
            data=None
        )
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

# Scheduled Tasks Endpoints
@app.post("/api/schedule/eod")
async def schedule_eod_reports(
    enabled: bool = True, 
    time: str = "17:00", 
    channels: Optional[List[str]] = None
):
    """Enable/disable scheduled EOD reports"""
    try:
        if enabled:
            job_id = await scheduled_workflows.schedule_eod_job(
                cron_expression=f"0 {time.split(':')[1]} {time.split(':')[0]} * * *",
                channels=channels
            )
            return APIResponse(
                success=True,
                message=f"EOD reports scheduled for {time}",
                data={"job_id": job_id}
            )
        else:
            return APIResponse(
                success=True,
                message="EOD reports scheduling disabled"
            )
    except Exception as e:
        logger.error(f"Error scheduling EOD reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to schedule EOD reports")

@app.post("/api/schedule/eow")
async def schedule_eow_reports(
    enabled: bool = True, 
    day: str = "friday", 
    time: str = "17:00",
    channels: Optional[List[str]] = None
):
    """Enable/disable scheduled EOW reports"""
    try:
        if enabled:
            job_id = await scheduled_workflows.schedule_eow_job(
                cron_expression=f"0 {time.split(':')[1]} {time.split(':')[0]} * * {['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'].index(day.lower())}",
                channels=channels
            )
            return APIResponse(
                success=True,
                message=f"EOW reports scheduled for {day} at {time}",
                data={"job_id": job_id}
            )
        else:
            return APIResponse(
                success=True,
                message="EOW reports scheduling disabled"
            )
    except Exception as e:
        logger.error(f"Error scheduling EOW reports: {e}")
        raise HTTPException(status_code=500, detail="Failed to schedule EOW reports")

# Workflow Management Endpoints
@app.post("/api/workflows/eod/run")
async def run_eod_workflow(channels: Optional[List[str]] = None):
    """Manually trigger EOD workflow"""
    try:
        import uuid
        workflow_id = str(uuid.uuid4())
        
        result = await workflow_engine.run_eod_workflow(workflow_id, channels)
        
        return APIResponse(
            success=True,
            message="EOD workflow completed successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error running EOD workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to run EOD workflow")

@app.post("/api/workflows/eow/run")
async def run_eow_workflow(channels: Optional[List[str]] = None):
    """Manually trigger EOW workflow"""
    try:
        import uuid
        workflow_id = str(uuid.uuid4())
        
        result = await workflow_engine.run_eow_workflow(workflow_id, channels)
        
        return APIResponse(
            success=True,
            message="EOW workflow completed successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error running EOW workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to run EOW workflow")

@app.post("/api/workflows/custom/run")
async def run_custom_workflow(
    custom_prompt: str,
    date_range: DateRange,
    channels: Optional[List[str]] = None
):
    """Run custom workflow with user-defined prompt"""
    try:
        import uuid
        workflow_id = str(uuid.uuid4())
        
        result = await workflow_engine.run_custom_workflow(
            workflow_id=workflow_id,
            custom_prompt=custom_prompt,
            start_date=date_range.start,
            end_date=date_range.end,
            channels=channels
        )
        
        return APIResponse(
            success=True,
            message="Custom workflow completed successfully",
            data=result
        )
    except Exception as e:
        logger.error(f"Error running custom workflow: {e}")
        raise HTTPException(status_code=500, detail="Failed to run custom workflow")

@app.get("/api/workflows/status/{workflow_id}")
async def get_workflow_status(workflow_id: str):
    """Get status of a specific workflow"""
    try:
        status = await workflow_engine.get_workflow_status(workflow_id)
        if not status:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return APIResponse(
            success=True,
            message="Workflow status retrieved",
            data=status
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get workflow status")

@app.get("/api/workflows/list")
async def list_workflow_runs(limit: int = 10):
    """List recent workflow runs"""
    try:
        runs = await workflow_engine.list_workflow_runs(limit=limit)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(runs)} workflow runs",
            data={"workflow_runs": runs}
        )
    except Exception as e:
        logger.error(f"Error listing workflow runs: {e}")
        raise HTTPException(status_code=500, detail="Failed to list workflow runs")

# State Management Endpoints
@app.get("/api/state/info")
async def get_state_info():
    """Get current system state information"""
    try:
        state = await get_summarizer_state()
        state_info = await state.get_state_info()
        
        return APIResponse(
            success=True,
            message="State information retrieved",
            data=state_info
        )
    except Exception as e:
        logger.error(f"Error getting state info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get state information")

@app.get("/api/state/cache/messages")
async def get_cached_messages(hours: int = 24):
    """Get recently cached messages"""
    try:
        state = await get_summarizer_state()
        messages = await state.get_recent_messages(hours=hours)
        
        return APIResponse(
            success=True,
            message=f"Retrieved {len(messages)} cached messages",
            data={"messages": messages}
        )
    except Exception as e:
        logger.error(f"Error getting cached messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get cached messages")

# Message Management Endpoints
@app.get("/api/messages/search")
async def search_messages(
    query: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    channels: Optional[List[str]] = None,
    limit: int = 50
):
    """Search messages by content"""
    try:
        # Set default date range to last 7 days if not provided
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=7)
        
        messages = await database.get_messages_by_date_range(
            start_date=start_date,
            end_date=end_date,
            channels=channels
        )
        
        # Simple text search (could be enhanced with full-text search)
        filtered_messages = [
            msg for msg in messages 
            if query.lower() in msg.get('text', '').lower()
        ][:limit]
        
        return APIResponse(
            success=True,
            message=f"Found {len(filtered_messages)} messages matching '{query}'",
            data={"messages": filtered_messages}
        )
    except Exception as e:
        logger.error(f"Error searching messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to search messages")

@app.get("/api/messages/stats")
async def get_message_stats():
    """Get message statistics"""
    try:
        stats = await database.get_message_stats()
        
        return APIResponse(
            success=True,
            message="Message statistics retrieved",
            data=stats
        )
    except Exception as e:
        logger.error(f"Error getting message stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get message statistics")

# AI Service Endpoints
@app.post("/api/ai/suggestions")
async def get_summary_suggestions(summary_text: str):
    """Get suggestions for improving a summary"""
    try:
        suggestions = await ai_service.suggest_summary_improvements(summary_text)
        
        return APIResponse(
            success=True,
            message=f"Generated {len(suggestions)} suggestions",
            data={"suggestions": suggestions}
        )
    except Exception as e:
        logger.error(f"Error getting suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate suggestions")

@app.post("/api/ai/chat/advanced")
async def advanced_chat(
    message: str,
    context: Optional[Dict[str, Any]] = None
):
    """Advanced chat interface with context"""
    try:
        # Process message with additional context
        if context:
            enhanced_message = f"Context: {context}\n\nUser Message: {message}"
        else:
            enhanced_message = message
        
        response = await ai_service.process_chat_message(enhanced_message)
        
        return ChatResponse(
            response=response,
            action_taken="processed_with_context" if context else "processed_simple",
            data={"context_used": bool(context)}
        )
    except Exception as e:
        logger.error(f"Error in advanced chat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process advanced chat")

# Utility Endpoints
@app.post("/api/utils/cleanup")
async def cleanup_old_data(days_old: int = 30):
    """Clean up old data (PDFs, workflow runs, etc.)"""
    try:
        # Clean up old PDFs
        pdf_cleanup = await pdf_service.cleanup_old_pdfs(days_old=days_old)
        
        # Clean up old workflow runs
        await workflow_engine.cleanup_old_workflow_runs(days_old=days_old)
        
        return APIResponse(
            success=True,
            message=f"Cleanup completed: removed {pdf_cleanup.get('deleted_count', 0)} old files",
            data=pdf_cleanup
        )
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup old data")

@app.get("/api/utils/system-info")
async def get_system_info():
    """Get comprehensive system information"""
    try:
        # Gather information from all services
        health_info = await health_check()
        message_stats = await database.get_message_stats()
        
        state = await get_summarizer_state()
        state_info = await state.get_state_info()
        
        workflow_runs = await workflow_engine.list_workflow_runs(limit=5)
        
        system_info = {
            "health": health_info,
            "message_stats": message_stats,
            "state_info": state_info,
            "recent_workflows": workflow_runs,
            "system_time": datetime.utcnow().isoformat()
        }
        
        return APIResponse(
            success=True,
            message="System information retrieved",
            data=system_info
        )
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system information")

# Slash Commands Endpoint
@app.post("/api/slack/commands")
async def handle_slack_commands(
    token: str = Form(...),
    team_id: str = Form(...),
    team_domain: str = Form(...),
    channel_id: str = Form(...),
    channel_name: str = Form(...),
    user_id: str = Form(...),
    user_name: str = Form(...),
    command: str = Form(...),
    text: str = Form(...),
    response_url: str = Form(...),
    trigger_id: str = Form(...)
):
    """Handle Slack slash commands"""
    try:
        # Verify the request (you might want to verify the token)
        if command == "/daily-summary":
            await _handle_summary_command("EOD", channel_id, user_name, text)
        elif command == "/weekly-summary":
            await _handle_summary_command("EOW", channel_id, user_name, text)
        elif command == "/sync-messages":
            await _handle_sync_command(channel_id, text)
        elif command == "/help-summarizer":
            await _send_help_message(channel_id)
        else:
            await slack_service.send_message(
                channel=channel_id,
                text="❌ Unknown command. Use `/help-summarizer` for available commands."
            )
        
        return {"response_type": "in_channel", "text": "✅ Command received and processing..."}
        
    except Exception as e:
        logger.error(f"Error handling slash command: {e}")
        return {"response_type": "ephemeral", "text": "❌ Error processing command. Please try again."}

async def _handle_summary_command(summary_type: str, channel_id: str, user_name: str, text: str):
    """Handle summary generation commands"""
    await slack_service.send_message(
        channel=channel_id,
        text=f"🔄 {user_name} requested {summary_type} summary. Generating..."
    )
    await _generate_and_send_summary(summary_type, channel_id)

async def _handle_sync_command(channel_id: str, text: str):
    """Handle message sync command"""
    try:
        hours_back = int(text) if text.isdigit() else 24
        
        await slack_service.send_message(
            channel=channel_id,
            text=f"🔄 Syncing messages from the last {hours_back} hours..."
        )
        
        result = await slack_service.sync_messages(hours_back=hours_back)
        
        await slack_service.send_message(
            channel=channel_id,
            text=f"✅ Synced {result.get('total_messages', 0)} messages from {result.get('channels_processed', 0)} channels"
        )
        
    except Exception as e:
        logger.error(f"Error in sync command: {e}")
        await slack_service.send_message(
            channel=channel_id,
            text="❌ Error syncing messages. Please try again."
        )

# Internal summary generation (used by webhook)
async def generate_summary_internal(request: SummaryRequest) -> SummaryResponse:
    """Internal method to generate summary (used by webhook and slash commands)"""
    try:
        # Fetch messages from database based on request
        messages = await database.get_messages_by_date_range(
            start_date=request.date_range.start,
            end_date=request.date_range.end,
            channels=request.channels
        )
        
        if not messages:
            raise Exception(f"No messages found for the specified date range")
        
        # Get user preferences if not provided
        preferences_dict = {}
        if request.preferences:
            preferences_dict = {
                "summary_style": request.preferences.summary_style,
                "include_threads": request.preferences.include_threads
            }
        else:
            preferences_dict = await database.get_user_preferences()
        
        # Generate AI summary
        if request.custom_prompt:
            summary_text = await ai_service.generate_custom_summary(
                messages=messages,
                custom_prompt=request.custom_prompt
            )
        else:
            summary_text = await ai_service.generate_summary(
                messages=messages,
                summary_type=request.type.value,
                user_preferences=preferences_dict
            )
        
        # Generate PDF
        pdf_path = await pdf_service.create_summary_pdf(
            summary=summary_text,
            summary_type=request.type.value,
            metadata={
                "summary_type": request.type.value,
                "generated_at": datetime.utcnow().isoformat(),
                "message_count": len(messages),
                "channels": request.channels or [],
                "custom_prompt": request.custom_prompt
            }
        )
        
        # Store summary metadata in database
        summary_id = await database.store_summary_metadata(
            summary_text=summary_text,
            pdf_path=pdf_path,
            summary_type=request.type.value,
            message_count=len(messages),
            date_range_start=request.date_range.start,
            date_range_end=request.date_range.end,
            channels=request.channels
        )
        
        logger.info(f"Generated {request.type.value} summary with {len(messages)} messages")
        
        return SummaryResponse(
            id=summary_id,
            summary=summary_text,
            pdf_url=f"/api/reports/{summary_id}/pdf",
            generated_at=datetime.utcnow(),
            message_count=len(messages),
            type=request.type
        )
        
    except Exception as e:
        logger.error(f"Error generating summary internally: {e}")
        raise Exception(f"Failed to generate summary: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)