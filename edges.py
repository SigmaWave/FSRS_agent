from state import LogState

def route_after_judgment(state: LogState) -> str:
    MAX_RETRIES = 2
    
    # If no pending items remain, or we've retried too many times
    if not state.get("pending_facts") or state.get("retry_count", 0) >= MAX_RETRIES:
        return "save_node"
    
    # Still have rejected facts that need breaking down
    return "split_node"