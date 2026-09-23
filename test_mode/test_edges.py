from test_mode.test_state import TestState

def route_fsrs(state: TestState) -> str:
    # If this was the initial pass and we found items, go to testing.
    # If no items were found, end. 
    # If this was the final pass (is_initial_pass is False), end.
    if state.get("is_initial_pass") is False:
        if not state.get("items_to_review"):
            return "end"
        # If we have items but no user answers yet, we must be entering the loop
        if "user_answer" not in state["items_to_review"][0]:
            return "testing_node"
        # Otherwise, we just finished the final DB save
        return "end"
    return "end"