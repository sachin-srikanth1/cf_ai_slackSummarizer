from motor.motor_asyncio import AsyncIOMotorClient
from beanie import Document, init_beanie
from pydantic import Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# MongoDB Document Models using Beanie
class SlackMessage(Document):
    id: str = Field(..., alias="_id")
    channel_id: str
    channel_name: str
    user_id: str
    username: str
    text: str
    timestamp: datetime
    thread_ts: Optional[str] = None
    reactions: Optional[List[Dict[str, Any]]] = []
    files: Optional[List[Dict[str, Any]]] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "slack_messages"
        indexes = [
            "channel_id",
            "timestamp",
            "user_id",
            [("channel_id", 1), ("timestamp", -1)],  # Compound index for queries
        ]

class Summary(Document):
    id: str = Field(..., alias="_id")
    type: str  # EOD or EOW
    summary_text: str
    pdf_path: Optional[str] = None
    message_count: int
    channels: Optional[List[str]] = []
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    date_range_start: datetime
    date_range_end: datetime

    class Settings:
        name = "summaries"
        indexes = [
            "type",
            "generated_at",
            [("type", 1), ("generated_at", -1)],
        ]

class UserPreferences(Document):
    id: str = Field(default="default", alias="_id")
    summary_style: str = "technical"
    include_threads: bool = True
    filter_channels: List[str] = []
    report_frequency: str = "daily"
    slack_user_id: Optional[str] = None
    notification_channel: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "user_preferences"

class Database:
    def __init__(self):
        self.mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
        self.database_name = os.getenv("DATABASE_NAME", "slack_summarizer")
        self.client: Optional[AsyncIOMotorClient] = None
        self.database = None

    async def init_db(self):
        """Initialize MongoDB connection and Beanie"""
        try:
            # Create MongoDB client
            self.client = AsyncIOMotorClient(self.mongodb_url)
            self.database = self.client[self.database_name]
            
            # Initialize Beanie with document models
            await init_beanie(
                database=self.database,
                document_models=[SlackMessage, Summary, UserPreferences]
            )
            
            # Create default user preferences if they don't exist
            existing_prefs = await UserPreferences.find_one(UserPreferences.id == "default")
            if not existing_prefs:
                default_prefs = UserPreferences()
                await default_prefs.save()
            
            logger.info("MongoDB database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """Check MongoDB health"""
        try:
            if not self.client:
                return {"status": "unhealthy", "error": "Database not initialized"}
            
            # Ping the database
            await self.client.admin.command('ping')
            
            # Count documents to verify connection
            message_count = await SlackMessage.count()
            summary_count = await Summary.count()
            
            return {
                "status": "healthy",
                "database": self.database_name,
                "message_count": message_count,
                "summary_count": summary_count
            }
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def close_db(self):
        """Close database connection"""
        if self.client:
            self.client.close()

    async def store_slack_message(self, message_data: Dict[str, Any]) -> bool:
        """Store a Slack message in the database"""
        try:
            # Check if message already exists to avoid duplicates
            existing = await SlackMessage.find_one(SlackMessage.id == message_data["id"])
            if existing:
                logger.debug(f"Message {message_data['id']} already exists, skipping")
                return True
            
            message = SlackMessage(**message_data)
            await message.save()
            return True
        except Exception as e:
            logger.error(f"Error storing Slack message: {e}")
            return False

    async def get_messages_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime, 
        channels: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get messages within a date range, optionally filtered by channels"""
        try:
            query = SlackMessage.find(
                SlackMessage.timestamp >= start_date,
                SlackMessage.timestamp <= end_date
            )
            
            if channels:
                query = query.find(SlackMessage.channel_id.in_(channels))
            
            messages = await query.sort("timestamp").to_list()
            
            return [
                {
                    "id": msg.id,
                    "channel_id": msg.channel_id,
                    "channel_name": msg.channel_name,
                    "user_id": msg.user_id,
                    "username": msg.username,
                    "text": msg.text,
                    "timestamp": msg.timestamp,
                    "thread_ts": msg.thread_ts,
                    "reactions": msg.reactions,
                    "files": msg.files
                }
                for msg in messages
            ]
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []

    async def store_summary_metadata(
        self, 
        summary_text: str, 
        pdf_path: str, 
        summary_type: str, 
        message_count: int,
        date_range_start: datetime,
        date_range_end: datetime,
        channels: Optional[List[str]] = None
    ) -> str:
        """Store summary metadata and return summary ID"""
        try:
            import uuid
            summary_id = str(uuid.uuid4())
            
            summary = Summary(
                id=summary_id,
                type=summary_type,
                summary_text=summary_text,
                pdf_path=pdf_path,
                message_count=message_count,
                channels=channels or [],
                date_range_start=date_range_start,
                date_range_end=date_range_end
            )
            await summary.save()
            return summary_id
        except Exception as e:
            logger.error(f"Error storing summary metadata: {e}")
            raise

    async def get_summary_history(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Get summary history"""
        try:
            summaries = await Summary.find().sort("-generated_at").skip(offset).limit(limit).to_list()
            
            return [
                {
                    "id": summary.id,
                    "type": summary.type,
                    "generated_at": summary.generated_at,
                    "message_count": summary.message_count,
                    "channels": summary.channels,
                    "summary_preview": summary.summary_text[:200] + "..." if len(summary.summary_text) > 200 else summary.summary_text
                }
                for summary in summaries
            ]
        except Exception as e:
            logger.error(f"Error fetching summary history: {e}")
            return []

    async def get_pdf_path(self, summary_id: str) -> Optional[str]:
        """Get PDF path for a summary"""
        try:
            summary = await Summary.find_one(Summary.id == summary_id)
            return summary.pdf_path if summary else None
        except Exception as e:
            logger.error(f"Error fetching PDF path: {e}")
            return None

    async def get_reports(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]:
        """Get list of all reports"""
        try:
            reports = await Summary.find().sort("-generated_at").skip(offset).limit(limit).to_list()
            
            return [
                {
                    "id": report.id,
                    "type": report.type,
                    "generated_at": report.generated_at,
                    "message_count": report.message_count,
                    "channels": report.channels,
                    "pdf_available": bool(report.pdf_path)
                }
                for report in reports
            ]
        except Exception as e:
            logger.error(f"Error fetching reports: {e}")
            return []

    async def get_user_preferences(self) -> Dict[str, Any]:
        """Get user preferences"""
        try:
            prefs = await UserPreferences.find_one(UserPreferences.id == "default")
            
            if not prefs:
                # Create default preferences
                prefs = UserPreferences()
                await prefs.save()
            
            return {
                "summary_style": prefs.summary_style,
                "include_threads": prefs.include_threads,
                "filter_channels": prefs.filter_channels,
                "report_frequency": prefs.report_frequency,
                "slack_user_id": prefs.slack_user_id,
                "notification_channel": prefs.notification_channel
            }
        except Exception as e:
            logger.error(f"Error fetching user preferences: {e}")
            return {}

    async def update_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        try:
            prefs = await UserPreferences.find_one(UserPreferences.id == "default")
            
            if not prefs:
                prefs = UserPreferences()
            
            # Update fields
            for key, value in preferences.items():
                if hasattr(prefs, key):
                    setattr(prefs, key, value)
            
            prefs.updated_at = datetime.utcnow()
            await prefs.save()
            return True
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return False

    async def get_message_stats(self) -> Dict[str, Any]:
        """Get message statistics"""
        try:
            total_messages = await SlackMessage.count()
            
            # Get messages from last 24 hours
            yesterday = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            recent_messages = await SlackMessage.find(
                SlackMessage.timestamp >= yesterday
            ).count()
            
            # Get unique channels
            pipeline = [
                {"$group": {"_id": "$channel_id", "count": {"$sum": 1}}},
                {"$count": "total_channels"}
            ]
            channel_result = await SlackMessage.aggregate(pipeline).to_list(1)
            unique_channels = channel_result[0]["total_channels"] if channel_result else 0
            
            return {
                "total_messages": total_messages,
                "recent_messages": recent_messages,
                "unique_channels": unique_channels
            }
        except Exception as e:
            logger.error(f"Error getting message stats: {e}")
            return {}

# Global database instance
database = Database()