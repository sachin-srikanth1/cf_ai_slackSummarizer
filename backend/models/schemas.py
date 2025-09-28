from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class SummaryType(str, Enum):
    EOD = "EOD"
    EOW = "EOW"

class SummaryStyle(str, Enum):
    TECHNICAL = "technical"
    EXECUTIVE = "executive"
    DETAILED = "detailed"

class ReportFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"

# Request/Response Models
class DateRange(BaseModel):
    start: datetime
    end: datetime

class UserPreferences(BaseModel):
    summary_style: SummaryStyle = SummaryStyle.TECHNICAL
    include_threads: bool = True
    filter_channels: List[str] = Field(default_factory=list)
    report_frequency: ReportFrequency = ReportFrequency.DAILY
    slack_user_id: Optional[str] = None
    notification_channel: Optional[str] = None

class SummaryRequest(BaseModel):
    type: SummaryType
    date_range: DateRange
    channels: Optional[List[str]] = None
    custom_prompt: Optional[str] = None
    preferences: Optional[UserPreferences] = None

class SummaryResponse(BaseModel):
    id: str
    summary: str
    pdf_url: str
    generated_at: datetime
    message_count: int
    type: SummaryType

class SlackMessage(BaseModel):
    id: str
    channel_id: str
    channel_name: str
    user_id: str
    username: str
    text: str
    timestamp: datetime
    thread_ts: Optional[str] = None
    reactions: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    files: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

class SlackChannel(BaseModel):
    id: str
    name: str
    is_private: bool = False
    member_count: Optional[int] = None

class ReportMetadata(BaseModel):
    id: str
    type: SummaryType
    generated_at: datetime
    message_count: int
    channels: List[str]
    pdf_path: str
    summary_preview: str = Field(max_length=200)

class ChatMessage(BaseModel):
    message: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ChatResponse(BaseModel):
    response: str
    action_taken: Optional[str] = None
    data: Optional[Dict[str, Any]] = None

class HealthStatus(BaseModel):
    status: str
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None