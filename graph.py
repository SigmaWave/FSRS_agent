from langgraph.graph import StateGraph, START, END
from state import LogState
from nodes import split_node

# 1. Initialize graph builder with the LogState schema
builder = StateGraph(LogState)

# 2. Register the node
builder.add_node("split_node", split_node)

# 3. Define the linear edge execution
builder.add_edge(START, "split_node")
builder.add_edge("split_node", END)

# 4. Compile the graph into an executable runnable
app = builder.compile()

# --- Execution & Verification ---
if __name__ == "__main__":
    # Visual verification: print Mermaid diagram definition
    print("--- Mermaid Graph Definition ---")
    print(app.get_graph().draw_mermaid())
    print("--------------------------------\n")

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
            "The French Revolution began in 1789 with the Storming of the Bastille. "
            "It eventually led to the rise of Napoleon Bonaparte, who declared himself Emperor in 1804."
        ),
        "pending_facts": [],
        "approved_facts": [],
        "retry_count": 0
    }

    print("\nRunning graph invocation...")
    output = app.invoke(sample_input)
    print("\nFinal State Output:")
    print(f"Extracted Facts: {output.get('pending_facts')}")
    print(f"Retry Count: {output.get('retry_count')}")