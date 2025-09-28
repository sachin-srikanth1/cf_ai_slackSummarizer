from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
from datetime import datetime, timedelta
import logging

from api.slack import SlackService
from api.ai import AIService
from api.pdf import PDFService
from models.database import database
from models.schemas import (
    SummaryRequest, 
    SummaryResponse, 
    UserPreferences, 
    SlackMessage,
    ReportMetadata
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Slack AI Summarizer API",
    description="API for generating AI-powered EOD/EOW summaries from Slack messages",
    version="1.0.0"
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
ai_service = AIService()
pdf_service = PDFService()

@app.on_event("startup")
async def startup_event():
    """Initialize database and services on startup"""
    await database.init_db()
    logger.info("Application started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    await database.close_db()
    logger.info("Application shutdown complete")

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
async def slack_webhook(payload: Dict[Any, Any]):
    """Handle incoming Slack webhooks"""
    # TODO: Verify Slack signature
    # TODO: Process different event types
    # TODO: Store messages in database
    logger.info(f"Received Slack webhook: {payload.get('type', 'unknown')}")
    return {"status": "received"}

@app.get("/api/slack/channels")
async def get_slack_channels():
    """Get list of available Slack channels"""
    try:
        channels = await slack_service.get_channels()
        return {"channels": channels}
    except Exception as e:
        logger.error(f"Error fetching channels: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch channels")

@app.post("/api/slack/sync")
async def sync_slack_messages(background_tasks: BackgroundTasks):
    """Manually trigger sync of Slack messages"""
    background_tasks.add_task(slack_service.sync_messages)
    return {"message": "Sync started in background"}

# Summary Generation Endpoints
@app.post("/api/summary/generate", response_model=SummaryResponse)
async def generate_summary(request: SummaryRequest):
    """Generate EOD/EOW summary"""
    try:
        # TODO: Fetch messages from database based on request
        messages = await database.get_messages_by_date_range(
            start_date=request.date_range.start,
            end_date=request.date_range.end,
            channels=request.channels
        )
        
        # TODO: Generate AI summary
        summary_text = await ai_service.generate_summary(
            messages=messages,
            summary_type=request.type,
            user_preferences=request.preferences
        )
        
        # TODO: Generate PDF
        pdf_path = await pdf_service.create_summary_pdf(
            summary=summary_text,
            summary_type=request.type,
            metadata={
                "generated_at": datetime.utcnow().isoformat(),
                "message_count": len(messages),
                "channels": request.channels or []
            }
        )
        
        # TODO: Store summary metadata in database
        summary_id = await database.store_summary_metadata(
            summary_text=summary_text,
            pdf_path=pdf_path,
            summary_type=request.type,
            message_count=len(messages)
        )
        
        return SummaryResponse(
            id=summary_id,
            summary=summary_text,
            pdf_url=f"/api/reports/{summary_id}/pdf",
            generated_at=datetime.utcnow(),
            message_count=len(messages),
            type=request.type
        )
        
    except Exception as e:
        logger.error(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")

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
async def chat_with_agent(message: str):
    """Chat interface for interacting with the agent"""
    try:
        # TODO: Process chat commands
        # TODO: Handle requests like "generate EOD report", "show preferences"
        response = await ai_service.process_chat_message(message)
        return {"response": response}
    except Exception as e:
        logger.error(f"Error processing chat message: {e}")
        raise HTTPException(status_code=500, detail="Failed to process message")

# Scheduled Tasks Endpoints
@app.post("/api/schedule/eod")
async def schedule_eod_reports(enabled: bool = True, time: str = "17:00"):
    """Enable/disable scheduled EOD reports"""
    # TODO: Configure scheduled task for EOD reports
    return {"message": f"EOD reports {'enabled' if enabled else 'disabled'} for {time}"}

@app.post("/api/schedule/eow")
async def schedule_eow_reports(enabled: bool = True, day: str = "friday", time: str = "17:00"):
    """Enable/disable scheduled EOW reports"""
    # TODO: Configure scheduled task for EOW reports
    return {"message": f"EOW reports {'enabled' if enabled else 'disabled'} for {day} at {time}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)