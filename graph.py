from langgraph.graph import StateGraph, START, END
from state import LogState
from nodes import split_node, judge_node, save_node
from edges import route_after_judgment
import json

builder = StateGraph(LogState)

builder.add_node("split_node", split_node)
builder.add_node("judge_node", judge_node)
builder.add_node("save_node", save_node)

builder.add_edge(START, "split_node")
builder.add_edge("split_node", "judge_node")

builder.add_conditional_edges(
    "judge_node",
    route_after_judgment,
    {
        "retry": "split_node",
        "save_node": "save_node"
    }
)
builder.add_edge("save_node", END)

app = builder.compile()

if __name__ == "__main__":
    try:
        png_data = app.get_graph().draw_mermaid_png()
        with open("graph.png", "wb") as f:
            f.write(png_data)
        print("Graph diagram saved to graph.png")
    except Exception as e:
        print(f"Could not render image file: {e}")

    # Test run with sample input
    sample_input = {
        "raw_input": (
            "America Independence, 4 July 1776 "
            ""
        ),
        "pending_items": [],
        "approved_items": [],
        "retry_count": 0,
    }

    print("Starting execution...\n")
    accumulated_state = dict(sample_input)

    for event in app.stream(sample_input, stream_mode="updates"):
        for node_name, state_patch in event.items():
            print(f"--- [Node: {node_name}] ---")
            for key, val in state_patch.items():
                print(f"{key}: {json.dumps(val, indent=2)}")
            accumulated_state.update(state_patch)

    print("\n================ FINAL SUMMARY ================")
    print("Approved Items:")
    print(json.dumps(accumulated_state.get("approved_items"), indent=2))
    
    pending = accumulated_state.get("pending_items")
    if pending:
        print("\nRejected / Pending Items:")
        print(json.dumps(pending, indent=2))
    print(f"\nTotal Retries: {accumulated_state.get('retry_count')}")