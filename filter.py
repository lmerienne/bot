from typing import Dict, Any

FILTERS = {
    "enabled_events": ["push", 
                    "pull_request", 
                    "pull_request_review", 
                    "create_branch_event", 
                    "delete_branch_event"],
                    
    "excluded_actions": ["synchronize"],
}

class MessageFilter:
    def __init__(self):
        self.filters = FILTERS
    
    def is_event_enabled(self, event_type: str, data: Dict[str, Any]) -> bool:
        if event_type not in self.filters["enabled_events"]:
            return False
        
        action = data.get("action", "")
        if action in self.filters["excluded_actions"]:
            return False
        
        return True

