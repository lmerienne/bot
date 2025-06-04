from typing import Dict, Any

FILTERS = {
    "enabled_events": ["push", 
                    "pull_request", 
                    "pull_request_review", 
                    "create_branch_event", 
                    "delete_branch_event"],
    
    "pull_request_actions": ["opened",
                            "reopened"],

    "excluded_actions": ["synchronize"],
}

class MessageFilter:
    def __init__(self):
        self.filters = FILTERS
    
    def is_event_enabled(self, event_type: str, data: Dict[str, Any]) -> bool:
        if event_type not in self.filters["enabled_events"]:
            return False
        
        action = data.get("action", "")
        if event_type == "pull_request":
            if action not in self.filters.get("pull_request_actions", []):
                return False
        if action in self.filters["excluded_actions"]:
            return False
        
        return True

