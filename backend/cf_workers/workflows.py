"""
Cloudflare Workflows integration for coordinating summary generation
Note: This is a Python representation of Cloudflare Workflows
The actual implementation would use Cloudflare's Workflow API
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SummaryWorkflow:
    """
    Workflow for generating and delivering Slack summaries
    In Cloudflare Workers, this would be implemented using the Workflows API
    """
    
    def __init__(self):
        self.workflow_runs = {}
    
    async def run_eod_workflow(self, workflow_id: str, channels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute End of Day workflow"""
        try:
            logger.info(f"Starting EOD workflow {workflow_id}")
            
            # Step 1: Calculate date range (today)
            end_time = datetime.utcnow()
            start_time = end_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # For demo purposes, return a mock result
            result = {
                'workflow_id': workflow_id,
                'status': 'completed',
                'type': 'EOD',
                'message_count': 0,
                'generated_at': datetime.utcnow().isoformat(),
                'date_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
            
            self.workflow_runs[workflow_id] = result
            logger.info(f"EOD workflow {workflow_id} completed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"EOD workflow {workflow_id} failed: {e}")
            error_result = {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e),
                'failed_at': datetime.utcnow().isoformat()
            }
            self.workflow_runs[workflow_id] = error_result
            raise
    
    async def run_eow_workflow(self, workflow_id: str, channels: Optional[List[str]] = None) -> Dict[str, Any]:
        """Execute End of Week workflow"""
        try:
            logger.info(f"Starting EOW workflow {workflow_id}")
            
            # Step 1: Calculate date range (this week)
            end_time = datetime.utcnow()
            # Start of current week (Monday)
            days_since_monday = end_time.weekday()
            start_time = end_time - timedelta(days=days_since_monday)
            start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # For demo purposes, return a mock result
            result = {
                'workflow_id': workflow_id,
                'status': 'completed',
                'type': 'EOW',
                'message_count': 0,
                'generated_at': datetime.utcnow().isoformat(),
                'date_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
            
            self.workflow_runs[workflow_id] = result
            logger.info(f"EOW workflow {workflow_id} completed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"EOW workflow {workflow_id} failed: {e}")
            error_result = {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e),
                'failed_at': datetime.utcnow().isoformat()
            }
            self.workflow_runs[workflow_id] = error_result
            raise
    
    async def run_custom_workflow(
        self, 
        workflow_id: str, 
        custom_prompt: str,
        start_date: datetime,
        end_date: datetime,
        channels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute custom workflow with user-defined parameters"""
        try:
            logger.info(f"Starting custom workflow {workflow_id}")
            
            # For demo purposes, return a mock result
            result = {
                'workflow_id': workflow_id,
                'status': 'completed',
                'type': 'CUSTOM',
                'message_count': 0,
                'custom_prompt': custom_prompt,
                'generated_at': datetime.utcnow().isoformat()
            }
            
            self.workflow_runs[workflow_id] = result
            logger.info(f"Custom workflow {workflow_id} completed successfully")
            
            return result
            
        except Exception as e:
            logger.error(f"Custom workflow {workflow_id} failed: {e}")
            error_result = {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e),
                'failed_at': datetime.utcnow().isoformat()
            }
            self.workflow_runs[workflow_id] = error_result
            raise
    
    async def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a workflow run"""
        return self.workflow_runs.get(workflow_id)
    
    async def list_workflow_runs(self, limit: int = 10) -> List[Dict[str, Any]]:
        """List recent workflow runs"""
        runs = list(self.workflow_runs.values())
        # Sort by generated_at or failed_at, most recent first
        runs.sort(key=lambda x: x.get('generated_at', x.get('failed_at', '')), reverse=True)
        return runs[:limit]
    
    async def cleanup_old_workflow_runs(self, days_old: int = 7):
        """Clean up old workflow run data"""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days_old)
            
            to_remove = []
            for workflow_id, run_data in self.workflow_runs.items():
                run_time_str = run_data.get('generated_at') or run_data.get('failed_at')
                if run_time_str:
                    try:
                        run_time = datetime.fromisoformat(run_time_str.replace('Z', '+00:00'))
                        if run_time < cutoff_time:
                            to_remove.append(workflow_id)
                    except ValueError:
                        # If we can't parse the date, remove it to be safe
                        to_remove.append(workflow_id)
            
            for workflow_id in to_remove:
                del self.workflow_runs[workflow_id]
            
            logger.info(f"Cleaned up {len(to_remove)} old workflow runs")
            
        except Exception as e:
            logger.error(f"Error cleaning up workflow runs: {e}")

class ScheduledWorkflows:
    """
    Manages scheduled workflows (cron-like functionality)
    In Cloudflare Workers, this would use Cron Triggers
    """
    
    def __init__(self):
        self.scheduled_jobs = {}
        self.workflow_engine = SummaryWorkflow()
    
    async def schedule_eod_job(self, cron_expression: str = "0 17 * * *", channels: Optional[List[str]] = None) -> str:
        """
        Schedule EOD report generation
        Default: Every day at 5 PM (0 17 * * *)
        """
        import uuid
        job_id = str(uuid.uuid4())
        
        job_config = {
            'id': job_id,
            'type': 'EOD',
            'cron': cron_expression,
            'channels': channels,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'active'
        }
        
        self.scheduled_jobs[job_id] = job_config
        logger.info(f"Scheduled EOD job {job_id} with cron '{cron_expression}'")
        
        return job_id
    
    async def schedule_eow_job(self, cron_expression: str = "0 17 * * 5", channels: Optional[List[str]] = None) -> str:
        """
        Schedule EOW report generation
        Default: Every Friday at 5 PM (0 17 * * 5)
        """
        import uuid
        job_id = str(uuid.uuid4())
        
        job_config = {
            'id': job_id,
            'type': 'EOW',
            'cron': cron_expression,
            'channels': channels,
            'created_at': datetime.utcnow().isoformat(),
            'status': 'active'
        }
        
        self.scheduled_jobs[job_id] = job_config
        logger.info(f"Scheduled EOW job {job_id} with cron '{cron_expression}'")
        
        return job_id

# Global instances
workflow_engine = SummaryWorkflow()
scheduled_workflows = ScheduledWorkflows()

async def get_workflow_engine() -> SummaryWorkflow:
    """Get the workflow engine instance"""
    return workflow_engine

async def get_scheduled_workflows() -> ScheduledWorkflows:
    """Get the scheduled workflows manager"""
    return scheduled_workflows