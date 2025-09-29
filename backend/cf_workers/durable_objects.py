"""
Durable Objects for state management in Cloudflare Workers
Note: This is a Python representation of the Cloudflare Workers TypeScript/JavaScript Durable Objects
The actual implementation would be in TypeScript for deployment to Cloudflare Workers
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SummarizerState:
    """
    Represents the state management for the Slack Summarizer
    In Cloudflare Workers, this would be implemented as a Durable Object
    """
    
    def __init__(self, state_id: str):
        self.state_id = state_id
        self.last_processed_timestamp = None
        self.message_cache = []
        self.user_preferences = {}
        self.active_workflows = {}
        self.rate_limits = {}
        
    async def initialize(self):
        """Initialize state from MongoDB"""
        try:
            # Load user preferences
            self.user_preferences = {}
            
            # Load last processed timestamp
            self.last_processed_timestamp = datetime.utcnow()
                
            logger.info(f"Initialized Durable Object state for {self.state_id}")
        except Exception as e:
            logger.error(f"Error initializing state: {e}")
    
    async def update_message_cache(self, messages: List[Dict[str, Any]]):
        """Update the message cache with new messages"""
        try:
            # Keep only recent messages in cache (last 1000)
            self.message_cache.extend(messages)
            self.message_cache = self.message_cache[-1000:]
            
            # Update last processed timestamp
            if messages:
                latest_timestamp = max(msg.get('timestamp', datetime.min) for msg in messages)
                if isinstance(latest_timestamp, datetime):
                    self.last_processed_timestamp = latest_timestamp
                    
            logger.info(f"Updated message cache with {len(messages)} new messages")
        except Exception as e:
            logger.error(f"Error updating message cache: {e}")
    
    async def get_recent_messages(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent messages from cache"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_messages = [
                msg for msg in self.message_cache 
                if msg.get('timestamp', datetime.min) >= cutoff_time
            ]
            return recent_messages
        except Exception as e:
            logger.error(f"Error getting recent messages: {e}")
            return []
    
    async def update_preferences(self, preferences: Dict[str, Any]):
        """Update user preferences"""
        try:
            self.user_preferences.update(preferences)
            logger.info("Updated user preferences in Durable Object state")
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
    
    async def get_preferences(self) -> Dict[str, Any]:
        """Get current user preferences"""
        return self.user_preferences
    
    async def register_workflow(self, workflow_id: str, workflow_type: str, schedule: str):
        """Register an active workflow"""
        try:
            self.active_workflows[workflow_id] = {
                'type': workflow_type,
                'schedule': schedule,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'active'
            }
            logger.info(f"Registered workflow {workflow_id} of type {workflow_type}")
        except Exception as e:
            logger.error(f"Error registering workflow: {e}")
    
    async def deregister_workflow(self, workflow_id: str):
        """Deregister a workflow"""
        try:
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
                logger.info(f"Deregistered workflow {workflow_id}")
        except Exception as e:
            logger.error(f"Error deregistering workflow: {e}")
    
    async def get_active_workflows(self) -> Dict[str, Any]:
        """Get all active workflows"""
        return self.active_workflows
    
    async def check_rate_limit(self, operation: str, limit_per_hour: int = 60) -> bool:
        """Check if operation is within rate limits"""
        try:
            current_hour = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
            hour_key = current_hour.isoformat()
            
            if operation not in self.rate_limits:
                self.rate_limits[operation] = {}
            
            current_count = self.rate_limits[operation].get(hour_key, 0)
            
            if current_count >= limit_per_hour:
                logger.warning(f"Rate limit exceeded for {operation}: {current_count}/{limit_per_hour}")
                return False
            
            self.rate_limits[operation][hour_key] = current_count + 1
            
            # Clean up old rate limit data (keep only last 24 hours)
            cutoff_time = current_hour - timedelta(hours=24)
            for op in self.rate_limits:
                self.rate_limits[op] = {
                    k: v for k, v in self.rate_limits[op].items()
                    if datetime.fromisoformat(k) >= cutoff_time
                }
            
            return True
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error
    
    async def get_state_info(self) -> Dict[str, Any]:
        """Get current state information"""
        return {
            'state_id': self.state_id,
            'last_processed_timestamp': self.last_processed_timestamp.isoformat() if self.last_processed_timestamp else None,
            'message_cache_size': len(self.message_cache),
            'active_workflows_count': len(self.active_workflows),
            'user_preferences': self.user_preferences,
            'rate_limits': {
                op: sum(counts.values()) for op, counts in self.rate_limits.items()
            }
        }

class WorkflowCoordinator:
    """
    Coordinates workflows and background tasks
    In Cloudflare Workers, this would be implemented using Workflows API
    """
    
    def __init__(self):
        self.active_workflows = {}
        self.workflow_history = []

# Global instances
global_state = None
global_coordinator = WorkflowCoordinator()

async def get_summarizer_state(state_id: str = "default") -> SummarizerState:
    """Get or create a Durable Object state instance"""
    global global_state
    
    if global_state is None or global_state.state_id != state_id:
        global_state = SummarizerState(state_id)
        await global_state.initialize()
    
    return global_state

async def get_workflow_coordinator() -> WorkflowCoordinator:
    """Get the workflow coordinator instance"""
    return global_coordinator