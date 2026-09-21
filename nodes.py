from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from state import LogState
from schema import ExtractedFacts

# 1. Initialize the client targeting your local endpoint
llm = ChatOpenAI(
    model="qwen2.5:14b",                  # Match your local model tag
    base_url="http://localhost:11434/v1",  # Local OpenAI-compatible endpoint
    api_key="not-needed",
    temperature=0.0
)

# 2. Bind structured output
structured_llm = llm.with_structured_output(ExtractedFacts)

# 3. Create the prompt template
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an expert knowledge engineer. Your task is to extract atomic facts "
        "from the provided text. Each fact must be self-contained, unambiguous, "
        "and testable as a single recall item."
    ),
    ("human", "{text_to_split}")
])

split_chain = prompt | structured_llm

def split_node(state: LogState) -> dict:
    # Check whether we are in a retry cycle or the first pass
    pending = state.get("pending_facts", [])
    
    if not pending:
        # First cycle: split raw_input
        source_text = state["raw_input"]
    else:
        # Retry cycle: combine rejected candidates into a single prompt for re-splitting
        source_text = "\n".join(pending)

    # Invoke chain
    result: ExtractedFacts = split_chain.invoke({"text_to_split": source_text})

    return {
        "pending_facts": result.facts,
        "retry_count": state.get("retry_count", 0) + 1
    }