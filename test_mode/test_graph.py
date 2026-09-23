import json
from langgraph.graph import StateGraph, START, END
from test_mode.test_state import TestState
from test_mode.test_nodes import fsrs_node, testing_node, communication_node, evaluation_node
from test_mode.test_edges import route_fsrs

builder = StateGraph(TestState)

builder.add_node("fsrs_node", fsrs_node)
builder.add_node("testing_node", testing_node)
builder.add_node("communication_node", communication_node)
builder.add_node("evaluation_node", evaluation_node)

builder.add_edge(START, "fsrs_node")
builder.add_conditional_edges(
    "fsrs_node",
    route_fsrs,
    {
        "testing_node": "testing_node",
        "end": END
    }
)
builder.add_edge("testing_node", "communication_node")
#TODO: conditional edge
builder.add_edge("communication_node", "evaluation_node")
builder.add_edge("evaluation_node", "fsrs_node")

app = builder.compile()

if __name__ == "__main__":
    print("Starting Testing Flow...\n")
    
    try:
        png_data = app.get_graph().draw_mermaid_png()
        with open("test_mode/graph.png", "wb") as f:
            f.write(png_data)
        print("Graph diagram saved to test_mode/graph.png")
    except Exception as e:
        print(f"Could not render image file: {e}")


    initial_state = {
        "items_to_review": [],
        "is_initial_pass": True
    }

    accumulated_state = dict(initial_state)

    for event in app.stream(initial_state, stream_mode="updates"):
        for node_name, state_patch in event.items():
            print(f"\n--- [Node Finished: {node_name}] ---")
            accumulated_state.update(state_patch)

    print("\n================ FINAL TEST SUMMARY ================")
    items = accumulated_state.get("items_to_review", [])
    if not items:
        print("No items currently due for review.")
    else:
        for item in items:
            print(f"\nID: {item['id']} | Category: {item['category']}")
            print(f"Query: {item.get('query')}")
            print(f"User Answer: {item.get('user_answer')}")
            print(f"Grade: {item.get('grade')} - {item.get('feedback')}")
