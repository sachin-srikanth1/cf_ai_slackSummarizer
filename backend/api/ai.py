import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        if not self.openai_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = AsyncOpenAI(api_key=self.openai_key)

    async def health_check(self) -> Dict[str, Any]:
        """Check OpenAI service availability"""
        if not self.client:
            return {
                "status": "unhealthy", 
                "error": "OpenAI API key not configured",
                "provider": "openai"
            }
        
        try:
            # Test OpenAI connection by listing models
            models = await self.client.models.list()
            return {
                "status": "healthy",
                "provider": "openai",
                "models_available": len(models.data) > 0
            }
        except Exception as e:
            logger.error(f"OpenAI health check failed: {e}")
            return {
                "status": "unhealthy", 
                "error": str(e),
                "provider": "openai"
            }

    async def generate_summary(
        self, 
        messages: List[Dict[str, Any]], 
        summary_type: str, 
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate AI summary from Slack messages using OpenAI"""
        if not self.client:
            raise Exception("OpenAI client not initialized")
        
        try:
            # Build prompt based on messages and preferences
            prompt = self._build_summary_prompt(messages, summary_type, user_preferences)
            
            # Generate summary using OpenAI GPT-4
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",  # Using cost-effective model
                messages=[
                    {
                        "role": "system", 
                        "content": "You are a helpful assistant that creates clear, actionable summaries from Slack messages for engineering teams."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                max_tokens=2000,
                temperature=0.3
            )
            
            return response.choices[0].message.content or "Unable to generate summary"
                    
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            raise Exception(f"Failed to generate summary: {e}")

    def _build_summary_prompt(
        self, 
        messages: List[Dict[str, Any]], 
        summary_type: str, 
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the prompt for AI summary generation"""
        
        # Base prompt template
        base_prompt = f"""You are an AI assistant that creates {summary_type} (End of {'Day' if summary_type == 'EOD' else 'Week'}) summaries from Slack messages for engineering teams.

Your task is to analyze the following Slack messages and create a comprehensive summary that would be useful for team standups and progress tracking.

"""
        
        # Add user preferences
        if user_preferences:
            style = user_preferences.get("summary_style", "technical")
            if style == "technical":
                base_prompt += "Focus on technical details, code changes, bugs, and implementation specifics.\n"
            elif style == "executive":
                base_prompt += "Focus on high-level progress, milestones, and business impact.\n"
            elif style == "detailed":
                base_prompt += "Provide comprehensive details including technical aspects, progress, and context.\n"
        
        base_prompt += """
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

"""
        
        # Add messages (limit to avoid token limits)
        for i, message in enumerate(messages[:50]):  # Limit to 50 messages
            timestamp = message.get("timestamp", "")
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime("%Y-%m-%d %H:%M")
            
            channel = message.get("channel_name", "unknown")
            username = message.get("username", "unknown")
            text = message.get("text", "")
            
            # Clean up text (remove mentions, links formatting, etc.)
            cleaned_text = self._clean_message_text(text)
            
            base_prompt += f"\n[{timestamp}] #{channel} - {username}: {cleaned_text}\n"
        
        if len(messages) > 50:
            base_prompt += f"\n... and {len(messages) - 50} more messages\n"
        
        base_prompt += """

Please create a clear, actionable summary that helps the team understand what happened and what's coming next. Use bullet points and clear headings. Keep it concise but informative.
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
        
        # Use OpenAI for more complex chat interactions
        if self.client:
            try:
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful AI assistant for a Slack summarization tool. Help users with generating reports, managing preferences, and understanding the system. Keep responses concise and actionable."
                        },
                        {
                            "role": "user",
                            "content": message
                        }
                    ],
                    max_tokens=200,
                    temperature=0.7
                )
                return response.choices[0].message.content or "I'm here to help with your Slack summaries!"
            except Exception as e:
                logger.error(f"Error in chat processing: {e}")
        
        # Default response
        return "I'm here to help you generate Slack summaries! Try asking for an 'EOD report' or 'EOW report', or say 'help' to see what I can do."

    async def generate_custom_summary(
        self, 
        messages: List[Dict[str, Any]], 
        custom_prompt: str
    ) -> str:
        """Generate summary with custom user prompt"""
        if not self.client:
            raise Exception("OpenAI client not initialized")
        
        try:
            # Combine custom prompt with message data
            full_prompt = f"""Custom Request: {custom_prompt}

Based on the following Slack messages, please fulfill the above request:

"""
            
            for message in messages[:30]:  # Limit for token management
                timestamp = message.get("timestamp", "")
                if isinstance(timestamp, datetime):
                    timestamp = timestamp.strftime("%Y-%m-%d %H:%M")
                
                channel = message.get("channel_name", "unknown")
                username = message.get("username", "unknown")
                text = self._clean_message_text(message.get("text", ""))
                
                full_prompt += f"[{timestamp}] #{channel} - {username}: {text}\n"
            
            # Use OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that can analyze Slack messages and respond to custom requests."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                max_tokens=1500,
                temperature=0.5
            )
            
            return response.choices[0].message.content or "Unable to process custom request"
                
        except Exception as e:
            logger.error(f"Error generating custom summary: {e}")
            raise Exception(f"Failed to generate custom summary: {e}")

    async def suggest_summary_improvements(self, summary: str) -> List[str]:
        """Suggest improvements for a generated summary"""
        if not self.client:
            return ["OpenAI client not available for suggestions"]
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at reviewing team summaries. Provide 3-5 specific, actionable suggestions to improve the given summary."
                    },
                    {
                        "role": "user",
                        "content": f"Please review this team summary and suggest improvements:\n\n{summary}"
                    }
                ],
                max_tokens=500,
                temperature=0.3
            )
            
            suggestions_text = response.choices[0].message.content or ""
            # Split into list of suggestions
            suggestions = [s.strip() for s in suggestions_text.split('\n') if s.strip() and not s.strip().startswith('#')]
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return [f"Error generating suggestions: {str(e)}"]