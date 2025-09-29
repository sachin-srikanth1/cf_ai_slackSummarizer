import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import httpx
import json

logger = logging.getLogger(__name__)

class CloudflareAIService:
    def __init__(self):
        self.account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        self.api_token = os.getenv("CLOUDFLARE_API_TOKEN")
        self.model_name = "@cf/meta/llama-3.3-70b-instruct-fp8-fast"  # Llama 3.3 on Workers AI
        
        if not self.account_id or not self.api_token:
            logger.warning("Cloudflare credentials not found in environment variables")
            self.base_url = None
        else:
            self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{self.account_id}/ai/run/{self.model_name}"

    async def health_check(self) -> Dict[str, Any]:
        """Check Cloudflare Workers AI service availability"""
        if not self.base_url:
            return {
                "status": "unhealthy", 
                "error": "Cloudflare credentials not configured",
                "provider": "cloudflare_workers_ai"
            }
        
        try:
            # Test connection with a simple prompt
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            test_payload = {
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "max_tokens": 10
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=test_payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "provider": "cloudflare_workers_ai",
                        "model": self.model_name
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "error": f"API returned {response.status_code}",
                        "provider": "cloudflare_workers_ai"
                    }
                    
        except Exception as e:
            logger.error(f"Cloudflare Workers AI health check failed: {e}")
            return {
                "status": "unhealthy", 
                "error": str(e),
                "provider": "cloudflare_workers_ai"
            }

    async def generate_summary(
        self, 
        messages: List[Dict[str, Any]], 
        summary_type: str, 
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate AI summary from Slack messages using Cloudflare Workers AI (Llama 3.3)"""
        if not self.base_url:
            raise Exception("Cloudflare Workers AI not configured")
        
        try:
            # Build prompt based on messages and preferences
            prompt = self._build_summary_prompt(messages, summary_type, user_preferences)
            
            # Call Cloudflare Workers AI
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant that creates clear, actionable summaries from Slack messages for engineering teams. Focus on being concise and well-organized."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.3,
                "top_p": 0.9
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Cloudflare API error: {response.status_code} - {response.text}")
                
                result = response.json()
                
                # Extract response from Cloudflare Workers AI format
                if "result" in result and "response" in result["result"]:
                    return result["result"]["response"]
                elif "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    logger.warning(f"Unexpected response format: {result}")
                    return "Unable to generate summary - unexpected response format"
                    
        except Exception as e:
            logger.error(f"Error generating summary with Cloudflare Workers AI: {e}")
            raise Exception(f"Failed to generate summary: {e}")

    def _build_summary_prompt(
        self, 
        messages: List[Dict[str, Any]], 
        summary_type: str, 
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the prompt for AI summary generation"""
        
        # Base prompt template
        base_prompt = f"""Create a {summary_type} (End of {'Day' if summary_type == 'EOD' else 'Week'}) summary from Slack messages for an engineering team.

Analyze the following messages and create a comprehensive summary for team standups and progress tracking.

"""
        
        # Add user preferences
        if user_preferences:
            style = user_preferences.get("summary_style", "technical")
            if style == "technical":
                base_prompt += "Focus on: technical details, code changes, bugs, implementation specifics.\n"
            elif style == "executive":
                base_prompt += "Focus on: high-level progress, milestones, business impact.\n"
            elif style == "detailed":
                base_prompt += "Focus on: comprehensive details including technical aspects, progress, and context.\n"
        
        base_prompt += """
Organize the summary with these sections:

## 🎯 Key Accomplishments
- Major achievements and completed tasks
- Important milestones reached

## 🔧 Technical Updates
- Code changes, deployments, technical work
- Bug fixes and technical decisions
- Infrastructure/tooling updates

## 🚨 Issues & Blockers
- Problems encountered and resolutions
- Current blockers needing attention

## 📋 Upcoming Priorities
- Next steps and planned work
- Focus items for next period

## 💬 Notable Discussions
- Important conversations and decisions
- Team coordination highlights

Slack Messages:

"""
        
        # Add messages (limit to avoid token limits)
        for i, message in enumerate(messages[:40]):  # Reduced for Llama 3.3 context
            timestamp = message.get("timestamp", "")
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M")
            
            channel = message.get("channel_name", "unknown")
            username = message.get("username", "unknown")
            text = message.get("text", "")
            
            # Clean up text
            cleaned_text = self._clean_message_text(text)
            
            base_prompt += f"\n[{timestamp}] #{channel} - {username}: {cleaned_text}\n"
        
        if len(messages) > 40:
            base_prompt += f"\n... and {len(messages) - 40} more messages\n"
        
        base_prompt += """

Create a clear, actionable summary with bullet points and headers. Keep it concise but informative.
"""
        
        return base_prompt

    def _clean_message_text(self, text: str) -> str:
        """Clean Slack message text for better AI processing"""
        import re
        
        # Remove user mentions
        text = re.sub(r'<@U[A-Z0-9]+>', '@user', text)
        
        # Remove channel mentions
        text = re.sub(r'<#C[A-Z0-9]+\|([^>]+)>', r'#\1', text)
        
        # Remove URLs
        text = re.sub(r'<http[s]?://[^|>]+\|([^>]+)>', r'\1', text)
        text = re.sub(r'<http[s]?://[^>]+>', '[link]', text)
        
        # Remove emoji codes
        text = re.sub(r':[a-zA-Z0-9_+-]+:', '', text)
        
        # Clean up extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()

    async def process_chat_message(self, message: str) -> str:
        """Process chat messages and determine appropriate response"""
        message_lower = message.lower()
        
        # Handle EOD report requests
        if any(keyword in message_lower for keyword in ["eod", "end of day", "daily report"]):
            return "I'll generate an EOD report for you. Please specify the date range or I'll use today's messages."
        
        # Handle EOW report requests
        if any(keyword in message_lower for keyword in ["eow", "end of week", "weekly report"]):
            return "I'll generate an EOW report for you. Please specify the date range or I'll use this week's messages."
        
        # Handle preferences requests
        if any(keyword in message_lower for keyword in ["preferences", "settings", "configure"]):
            return "You can update your preferences for summary style, channels to include, and notification settings."
        
        # Handle help requests
        if any(keyword in message_lower for keyword in ["help", "what can you do", "commands"]):
            return """I can help you with:
            
🔹 **Generate Reports**: Ask for "EOD report" or "EOW report"
🔹 **View History**: "Show me past summaries"
🔹 **Update Settings**: "Change my preferences"
🔹 **Sync Messages**: "Sync recent Slack messages"

Just ask me in natural language and I'll help you out!"""
        
        # Use Cloudflare Workers AI for more complex chat interactions
        if self.base_url:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a helpful AI assistant for a Slack summarization tool. Help users with generating reports, managing preferences, and understanding the system. Keep responses concise and actionable."
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ],
                    "max_tokens": 200,
                    "temperature": 0.7
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        self.base_url,
                        headers=headers,
                        json=payload,
                        timeout=30.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        if "result" in result and "response" in result["result"]:
                            return result["result"]["response"]
                        elif "choices" in result and len(result["choices"]) > 0:
                            return result["choices"][0]["message"]["content"]
                
            except Exception as e:
                logger.error(f"Error in chat processing with Cloudflare Workers AI: {e}")
        
        # Default response
        return "I'm here to help you generate Slack summaries! Try asking for an 'EOD report' or 'EOW report', or say 'help' to see what I can do."

    async def generate_custom_summary(
        self, 
        messages: List[Dict[str, Any]], 
        custom_prompt: str
    ) -> str:
        """Generate summary with custom user prompt"""
        if not self.base_url:
            raise Exception("Cloudflare Workers AI not configured")
        
        try:
            # Combine custom prompt with message data
            full_prompt = f"""Custom Request: {custom_prompt}

Based on the following Slack messages, please fulfill the above request:

"""
            
            for message in messages[:25]:  # Limit for token management
                timestamp = message.get("timestamp", "")
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.strftime("%Y-%m-%d %H:%M")
                
                channel = message.get("channel_name", "unknown")
                username = message.get("username", "unknown")
                text = self._clean_message_text(message.get("text", ""))
                
                full_prompt += f"[{timestamp}] #{channel} - {username}: {text}\n"
            
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that can analyze Slack messages and respond to custom requests."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                "max_tokens": 1500,
                "temperature": 0.5
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code != 200:
                    raise Exception(f"Cloudflare API error: {response.status_code}")
                
                result = response.json()
                if "result" in result and "response" in result["result"]:
                    return result["result"]["response"]
                elif "choices" in result and len(result["choices"]) > 0:
                    return result["choices"][0]["message"]["content"]
                else:
                    return "Unable to process custom request"
                
        except Exception as e:
            logger.error(f"Error generating custom summary: {e}")
            raise Exception(f"Failed to generate custom summary: {e}")

    async def suggest_summary_improvements(self, summary: str) -> List[str]:
        """Suggest improvements for a generated summary"""
        if not self.base_url:
            return ["Cloudflare Workers AI not available for suggestions"]
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert at reviewing team summaries. Provide 3-5 specific, actionable suggestions to improve the given summary."
                    },
                    {
                        "role": "user",
                        "content": f"Please review this team summary and suggest improvements:\n\n{summary}"
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    suggestions_text = ""
                    
                    if "result" in result and "response" in result["result"]:
                        suggestions_text = result["result"]["response"]
                    elif "choices" in result and len(result["choices"]) > 0:
                        suggestions_text = result["choices"][0]["message"]["content"]
                    
                    # Split into list of suggestions
                    suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip() and not s.strip().startswith('#')]
                    return suggestions[:5]  # Limit to 5 suggestions
                
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
        
        return [f"Error generating suggestions: unable to connect to Cloudflare Workers AI"]

# Create alias for backwards compatibility
AIService = CloudflareAIService