from input_mode.state import LogState

def route_after_judgment(state: LogState) -> str:
    MAX_RETRIES = 2
    
    if not state.get("pending_items") or state.get("retry_count", 0) >= MAX_RETRIES:
        return "save_node"
    
    return "retry"