import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from input_mode.state import LogState
from input_mode.schema import ExtractedData, CategoryVerdict
from db import insert_approved_items

llm = ChatOpenAI(
    model="qwen2.5:14b",
    base_url="http://localhost:11434/v1",
    api_key="not-needed",
    temperature=0.0
)

structured_split = llm.with_structured_output(ExtractedData)
structured_judge = llm.with_structured_output(CategoryVerdict)

split_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Decompose the input into distinct entries. Assign exactly one category per entry: 'citation', 'date', 'coding', or 'unknown'.\n\n"
        "Extraction Rules:\n"
        "- 'citation': Extract 'quote' and 'author'. (e.g., quote='I think, therefore I am', author='Descartes')\n"
        "- 'date': Extract 'event' and 'date'. (e.g., event='Apollo 11 Moon landing', date='1969')\n"
        "- 'coding': Extract 'command' and 'description'. (e.g., command='ls -la', description='lists all files including hidden ones')\n"
        "- 'unknown': Extract raw text into 'text'.\n\n"
        "If provided with feedback on rejected items, fix the extraction based on that feedback."
    ),
    ("human", "{input_data}")
])

judge_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Evaluate whether the provided item is categorized correctly and if the appropriate fields are populated for that category.\n"
        "- A 'citation' must have 'quote' and 'author'.\n"
        "- A 'date' must have 'event' and 'date'.\n"
        "- A 'coding' concept must have 'command' and 'description'.\n\n"
        "Strictly ignore any other fields if they are empty strings (\"\") or null. Do not reject an item for having empty irrelevant fields.\n\n"
        "Return is_correct=True if valid. If invalid, return is_correct=False and explain the mismatch."
    ),
    ("human", "Item Data: {item_json}")
])



def split_node(state: LogState) -> dict:
    pending = state.get("pending_items", [])
    
    if not pending:
        input_data = state["raw_input"]
    else:
        input_data = "Fix these rejected items based on feedback:\n" + json.dumps(pending)

    res = (split_prompt | structured_split).invoke({"input_data": input_data})
    
    formatted_pending = []
    for item in res.items:
        item_dict = item.model_dump(exclude_none=True)
        item_dict["feedback"] = ""
        formatted_pending.append(item_dict)
        
    return {
        "pending_items": formatted_pending,
        "retry_count": state.get("retry_count", 0) + 1
    }

def judge_node(state: LogState) -> dict:
    pending = state.get("pending_items", [])
    approved = list(state.get("approved_items", []))
    still_pending = []

    for item in pending:
        eval_item = {k: v for k, v in item.items() if k != "feedback"}
        verdict = (judge_prompt | structured_judge).invoke({"item_json": json.dumps(eval_item)})
        
        if verdict.is_correct:
            approved.append(eval_item)
        else:
            eval_item["feedback"] = verdict.reason
            still_pending.append(eval_item)

    return {
        "approved_items": approved,
        "pending_items": still_pending
    }

def save_node(state: LogState) -> dict:
    approved = state.get("approved_items", [])
    raw_input = state.get("raw_input", "")
    
    if approved:
        insert_approved_items(raw_input, approved)
        
    return state