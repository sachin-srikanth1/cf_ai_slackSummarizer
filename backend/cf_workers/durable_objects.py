from typing import Dict, Any
from datetime import datetime


async def get_summarizer_state() -> Dict[str, Any]:
    return {
        "status": "active",
        "last_updated": datetime.utcnow().isoformat(),
        "processed_messages": 0,
        "active_workflows": 0
    }


async def get_workflow_coordinator() -> Dict[str, Any]:
    return {
        "status": "active",
        "coordinator_id": "default",
        "last_updated": datetime.utcnow().isoformat()
    }