import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import asyncio

logger = logging.getLogger(__name__)

class SlackService:
    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.signing_secret = os.getenv("SLACK_SIGNING_SECRET")
        
        if not self.bot_token:
            logger.warning("SLACK_BOT_TOKEN not found in environment variables")
            self.client = None
        else:
            self.client = WebClient(token=self.bot_token)

    async def health_check(self) -> Dict[str, Any]:
        """Check Slack API connectivity"""
        if not self.client:
            return {"status": "unhealthy", "error": "No Slack token configured"}
        
        try:
            response = self.client.auth_test()
            return {
                "status": "healthy",
                "bot_id": response.get("bot_id"),
                "team": response.get("team"),
                "user": response.get("user")
            }
        except SlackApiError as e:
            logger.error(f"Slack health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    async def get_channels(self) -> List[Dict[str, Any]]:
        """Get list of all channels the bot has access to"""
        if not self.client:
            raise Exception("Slack client not initialized")
        
        try:
            channels = []
            cursor = None
            
            while True:
                response = self.client.conversations_list(
                    cursor=cursor,
                    exclude_archived=True,
                    types="public_channel,private_channel"
                )
                
                for channel in response["channels"]:
                    channels.append({
                        "id": channel["id"],
                        "name": channel["name"],
                        "is_private": channel.get("is_private", False),
                        "member_count": channel.get("num_members", 0)
                    })
                
                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
            
            logger.info(f"Retrieved {len(channels)} channels")
            return channels
            
        except SlackApiError as e:
            logger.error(f"Error fetching channels: {e}")
            raise Exception(f"Failed to fetch channels: {e}")

    async def get_messages_from_channel(
        self, 
        channel_id: str, 
        start_time: datetime, 
        end_time: datetime,
        include_threads: bool = True
    ) -> List[Dict[str, Any]]:
        """Get messages from a specific channel within a time range"""
        if not self.client:
            raise Exception("Slack client not initialized")
        
        try:
            messages = []
            cursor = None
            
            # Convert datetime to Slack timestamp format
            oldest = start_time.timestamp()
            latest = end_time.timestamp()
            
            while True:
                response = self.client.conversations_history(
                    channel=channel_id,
                    oldest=str(oldest),
                    latest=str(latest),
                    cursor=cursor,
                    limit=200
                )
                
                for message in response["messages"]:
                    # Skip bot messages and system messages
                    if message.get("subtype") in ["bot_message", "channel_join", "channel_leave"]:
                        continue
                    
                    processed_message = await self._process_message(message, channel_id)
                    if processed_message:
                        messages.append(processed_message)
                    
                    # Get thread replies if requested
                    if include_threads and message.get("thread_ts") and message.get("reply_count", 0) > 0:
                        thread_messages = await self._get_thread_messages(
                            channel_id, 
                            message["thread_ts"]
                        )
                        messages.extend(thread_messages)
                
                cursor = response.get("response_metadata", {}).get("next_cursor")
                if not cursor:
                    break
            
            logger.info(f"Retrieved {len(messages)} messages from channel {channel_id}")
            return messages
            
        except SlackApiError as e:
            logger.error(f"Error fetching messages from channel {channel_id}: {e}")
            return []

    async def _get_thread_messages(self, channel_id: str, thread_ts: str) -> List[Dict[str, Any]]:
        """Get messages from a thread"""
        try:
            response = self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts
            )
            
            thread_messages = []
            for message in response["messages"][1:]:  # Skip the parent message
                processed_message = await self._process_message(message, channel_id, thread_ts)
                if processed_message:
                    thread_messages.append(processed_message)
            
            return thread_messages
            
        except SlackApiError as e:
            logger.error(f"Error fetching thread messages: {e}")
            return []

    async def _process_message(
        self, 
        message: Dict[str, Any], 
        channel_id: str, 
        thread_ts: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Process and format a Slack message"""
        try:
            # Get user info
            user_info = await self._get_user_info(message.get("user"))
            
            # Get channel info
            channel_info = await self._get_channel_info(channel_id)
            
            return {
                "id": message.get("ts"),
                "channel_id": channel_id,
                "channel_name": channel_info.get("name", "unknown"),
                "user_id": message.get("user"),
                "username": user_info.get("name", "unknown"),
                "text": message.get("text", ""),
                "timestamp": datetime.fromtimestamp(float(message.get("ts", 0))),
                "thread_ts": thread_ts or message.get("thread_ts"),
                "reactions": message.get("reactions", []),
                "files": message.get("files", [])
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return None

    async def _get_user_info(self, user_id: str) -> Dict[str, Any]:
        """Get user information (with caching)"""
        # TODO: Implement caching to avoid repeated API calls
        try:
            if not user_id:
                return {"name": "unknown"}
            
            response = self.client.users_info(user=user_id)
            user = response["user"]
            return {
                "name": user.get("name", "unknown"),
                "real_name": user.get("real_name", ""),
                "display_name": user.get("profile", {}).get("display_name", "")
            }
        except SlackApiError:
            return {"name": "unknown"}

    async def _get_channel_info(self, channel_id: str) -> Dict[str, Any]:
        """Get channel information (with caching)"""
        # TODO: Implement caching to avoid repeated API calls
        try:
            response = self.client.conversations_info(channel=channel_id)
            channel = response["channel"]
            return {
                "name": channel.get("name", "unknown"),
                "is_private": channel.get("is_private", False)
            }
        except SlackApiError:
            return {"name": "unknown"}

    async def sync_messages(self, hours_back: int = 24) -> Dict[str, Any]:
        """Sync messages from all channels for the specified time period"""
        if not self.client:
            raise Exception("Slack client not initialized")
        
        try:
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours_back)
            
            # Get all channels
            channels = await self.get_channels()
            
            total_messages = 0
            processed_channels = 0
            
            for channel in channels:
                try:
                    messages = await self.get_messages_from_channel(
                        channel["id"], 
                        start_time, 
                        end_time
                    )
                    
                    # Store messages in database
                    from models.database import database
                    stored_count = 0
                    for message in messages:
                        if await database.store_slack_message(message):
                            stored_count += 1
                    
                    total_messages += stored_count
                    processed_channels += 1
                    
                    logger.info(f"Synced {len(messages)} messages from #{channel['name']}")
                    
                except Exception as e:
                    logger.error(f"Error syncing channel {channel['name']}: {e}")
                    continue
            
            return {
                "success": True,
                "channels_processed": processed_channels,
                "total_messages": total_messages,
                "time_range": {
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Error during message sync: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def send_message(self, channel: str, text: str, thread_ts: Optional[str] = None) -> bool:
        """Send a message to a Slack channel"""
        if not self.client:
            raise Exception("Slack client not initialized")
        
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                thread_ts=thread_ts
            )
            return response.get("ok", False)
            
        except SlackApiError as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def upload_file(
        self, 
        channel: str, 
        file_path: str, 
        title: str, 
        initial_comment: Optional[str] = None
    ) -> bool:
        """Upload a file to a Slack channel"""
        if not self.client:
            raise Exception("Slack client not initialized")
        
        try:
            response = self.client.files_upload(
                channels=channel,
                file=file_path,
                title=title,
                initial_comment=initial_comment
            )
            return response.get("ok", False)
            
        except SlackApiError as e:
            logger.error(f"Error uploading file: {e}")
            return False

    def verify_signature(self, timestamp: str, signature: str, body: bytes) -> bool:
        """Verify Slack request signature"""
        if not self.signing_secret:
            logger.warning("SLACK_SIGNING_SECRET not configured")
            return False
        
        # TODO: Implement signature verification
        # This is important for production security
        import hmac
        import hashlib
        
        basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
        my_signature = 'v0=' + hmac.new(
            self.signing_secret.encode(),
            basestring.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(my_signature, signature)