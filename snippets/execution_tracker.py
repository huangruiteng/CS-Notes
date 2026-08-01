
#!/usr/bin/env python3
"""
Execution Tracker - Track tasks executed between user interactions
"""

import json
import os
from datetime import datetime

# Configuration
STATE_FILE = ".trae/todos/execution_state.json"
MAX_TASKS_BETWEEN_INTERVENTIONS = 8

def load_state():
    """Load execution state from file"""
    if not os.path.exists(STATE_FILE):
        return {
            "last_user_interaction_at": datetime.now().isoformat(),
            "tasks_executed_since_last_interaction": 0
        }
    
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state):
    """Save execution state to file"""
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)

def reset_on_user_interaction():
    """Reset state on user interaction"""
    state = load_state()
    state["last_user_interaction_at"] = datetime.now().isoformat()
    state["tasks_executed_since_last_interaction"] = 0
    save_state(state)
    print("✅ Reset execution state on user interaction")

def can_execute_more_tasks():
    """Check if we can execute more tasks"""
    state = load_state()
    return state["tasks_executed_since_last_interaction"] < MAX_TASKS_BETWEEN_INTERVENTIONS

def increment_task_count():
    """Increment task count"""
    state = load_state()
    state["tasks_executed_since_last_interaction"] += 1
    save_state(state)
    print(f"✅ Task count incremented to {state['tasks_executed_since_last_interaction']}")

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Execution Tracker")
    parser.add_argument("action", choices=["reset", "check", "increment"], help="Action to perform")
    args = parser.parse_args()

    if args.action == "reset":
        reset_on_user_interaction()
    elif args.action == "check":
        if can_execute_more_tasks():
            state = load_state()
            print(f"✅ Can execute more tasks! Current: {state['tasks_executed_since_last_interaction']}/{MAX_TASKS_BETWEEN_INTERVENTIONS}")
        else:
            state = load_state()
            print(f"⚠️  Max tasks reached! Current: {state['tasks_executed_since_last_interaction']}/{MAX_TASKS_BETWEEN_INTERVENTIONS}")
    elif args.action == "increment":
        increment_task_count()

if __name__ == "__main__":
    main()

