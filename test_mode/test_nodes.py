import os
import asyncio
import psycopg2
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from fsrs import Scheduler, Card, Rating
from datetime import datetime, timezone
from telegram import Bot

from test_mode.test_state import TestState
from test_mode.test_schema import CitationSubject, CommandGoal, GradeEvaluation

load_dotenv()
DB_URL = os.getenv("DATABASE_URL")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

llm = ChatOpenAI(model="qwen2.5:14b", 
                 base_url="http://localhost:11434/v1", 
                 api_key="not-needed", temperature=0.0)
fsrs_algo = Scheduler()

# --- Prompts ---
citation_prompt = ChatPromptTemplate.from_messages([
    ("system", "Identify the core subject of the following citation. Return only the subject."),
    ("human", "{quote}")
])

command_prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract the main goal from the following command description. Keep it concise."),
    ("human", "{description}")
])

#TODO: refactor for a more subjective evaluation by the LLM that is independent of the piece of knowledge tested
eval_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a strict grading evaluator for a spaced repetition system. Grade the user's answer from 1 to 4 based ONLY on the following rules:

Citation:
4: Identical to the original quote (minor spelling errors allowed).
3: A few different words, but the exact meaning is preserved.
2: Meaning is slightly altered OR sentence structure is different.
1: Meaning is radically different, citation is partial, or user doesn't know.

Date:
4: Exact date.
3: Within a few years OR correct year but missing month/day.
2: Within 10 years.
1: Greater than 10 years off or doesn't know.

Command ("How to do X?"):
4: Exact command.
3: Minor spelling error in the command.
2: Some words/flags are missing.
1: Different words used or incorrect command.

Command ("What does X do?"):
4: Covers all of the original description regardless of wording.
3: Partial coverage but >50% complete.
2: Partial coverage but <50% complete.
1: User doesn't know or states incorrect information.
"""),
    ("human", "Category: {category}\nOriginal Data: {original_data}\nQuery: {query}\nUser Answer: {user_answer}")
])

structured_citation = llm.with_structured_output(CitationSubject)
structured_command = llm.with_structured_output(CommandGoal)
structured_eval = llm.with_structured_output(GradeEvaluation)

# --- Nodes ---
def fsrs_node(state: TestState) -> dict:
    conn = psycopg2.connect(DB_URL)
    conn.autocommit = True
    
    if state.get("is_initial_pass", True):
        # Initial pass: Fetch rows due for review or newly added (next_review IS NULL)
        items = []
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, category, quote, author, event, date, command, description, stability, difficulty
                    FROM Knowledge 
                    WHERE next_review IS NULL OR next_review <= CURRENT_TIMESTAMP
                """)
                for row in cur.fetchall():
                    items.append({
                        "id": row[0], "category": row[1], "quote": row[2], "author": row[3],
                        "event": row[4], "date": row[5], "command": row[6], "description": row[7],
                        "stability": row[8], "difficulty": row[9]
                    })
        finally:
            conn.close()
        return {"items_to_review": items, "is_initial_pass": False}
    
    else:
        # Final pass: Apply FSRS updates based on grades and save to DB
        items = state.get("items_to_review", [])
        try:
            with conn.cursor() as cur:
                for item in items:
                    if not item.get("grade"):
                        #TODO: redirect to evaluation node
                        continue
                        
                    # Reconstruct FSRS Card state
                    card = Card()
                    if item.get("stability") is not None and item.get("difficulty") is not None:
                        card.stability = item["stability"]
                        card.difficulty = item["difficulty"]
                    
                    # Map 1-4 to FSRS Rating enum (1:Again, 2:Hard, 3:Good, 4:Easy)
                    rating = Rating(item["grade"])
                    
                    # Compute next state
                    card, _ = fsrs_algo.review_card(card, rating)
                    
                    # Update Knowledge Table
                    cur.execute("""
                        UPDATE Knowledge 
                        SET last_review = %s, next_review = %s, stability = %s, difficulty = %s
                        WHERE id = %s
                    """, (datetime.now(timezone.utc), card.due, card.stability, card.difficulty, item["id"]))
                    
                    # Insert Test log
                    cur.execute("""
                        INSERT INTO Test (id_knowledge, grade, feedback)
                        VALUES (%s, %s, %s)
                    """, (item["id"], item["grade"], item["feedback"]))
        finally:
            conn.close()
            
        return state

def testing_node(state: TestState) -> dict:
    import random
    items = state.get("items_to_review", [])
    
    for item in items:
        cat = item["category"]
        if cat == "citation":
            res = (citation_prompt | structured_citation).invoke({"quote": item["quote"]})
            item["query"] = f"Citation of {item['author']} on {res.subject}"
            
        elif cat == "date":
            item["query"] = f"When did {item['event']} happen?"
            
        elif cat == "coding":
            # Randomly choose between "How to do X" and "What does Y do"
            if random.choice([True, False]):
                res = (command_prompt | structured_command).invoke({"description": item["description"]})
                item["query"] = f"How to do: {res.main_goal}"
            else:
                item["query"] = f"What does the command `{item['command']}` do?"
                
    return {"items_to_review": items}

async def wait_for_reply(bot: Bot, chat_id: int) -> str:
    """
    Sends long-polling requests until a new text message 
    from the designated chat_id is received.
    """
    updates = await bot.get_updates(offset=-1, timeout=1)
    offset = (updates[-1].update_id + 1) if updates else None

    while True:
        updates = await bot.get_updates(offset=offset, timeout=30)
        for update in updates:
            offset = update.update_id + 1
            if update.message and update.message.chat_id == chat_id and update.message.text:
                return update.message.text.strip()
        await asyncio.sleep(1)

async def run_telegram_loop(items: list[dict], token: str, chat_id: int) -> list[dict]:
    async with Bot(token=token) as bot:
        for idx, item in enumerate(items, start=1):
            prompt_message = f"Card {idx}/{len(items)}:\n\n{item['query']}"
            await bot.send_message(chat_id=chat_id, text=prompt_message)
            
            user_reply = await wait_for_reply(bot, chat_id)
            item["user_answer"] = user_reply

            # Immediate acknowledgment
            #TODO: go to evaluation node and back to provide live feedback
            await bot.send_message(chat_id=chat_id, text="Recorded! Evaluating...")
            
    return items

def communication_node(state: TestState) -> dict:
    """
    Sends each query to Telegram, awaits the user's reply via long polling,
    and attaches the response to the state items.
    """
    items = state.get("items_to_review", [])
    if not items:
        return state

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID in environment.")

    chat_id = int(TELEGRAM_CHAT_ID)

    # Run the async loop inside the sync LangGraph node
    updated_items = asyncio.run(run_telegram_loop(items, TELEGRAM_BOT_TOKEN, chat_id))

    return {"items_to_review": updated_items}

def evaluation_node(state: TestState) -> dict:
    items = state.get("items_to_review", [])
    
    for item in items:
        original_data = {k: v for k, v in item.items() if k in ["quote", "author", "event", "date", "command", "description"] and v is not None}
        
        res = (eval_prompt | structured_eval).invoke({
            "category": item["category"],
            "original_data": str(original_data),
            "query": item["query"],
            "user_answer": item["user_answer"]
        })
        
        item["grade"] = res.grade
        item["feedback"] = res.feedback
        
    return {"items_to_review": items}