# 🐛 Debug Environment — OpenEnv RL Environment

A Reinforcement Learning environment where AI agents learn to **find and fix bugs in Python code**. Built on [OpenEnv](https://github.com/meta-pytorch/OpenEnv) by Meta & Hugging Face.

---

## 📌 Overview

The Debug Environment presents an AI agent with a **broken Python function** and challenges it to return a corrected version. The environment automatically executes the fix against test cases and assigns a reward based on correctness and efficiency.

Every episode generates a **fresh, unique challenge** using the Gemini API — making this a truly infinite, non-repeating training environment. If the API is unavailable, it gracefully falls back to a curated set of static challenges.

---

## 🎯 Task Description

| Property | Value |
|---|---|
| **Task** | Fix a buggy Python function |
| **Input** | Buggy code + error message + task description |
| **Output** | Corrected Python code |
| **Reward** | 0.0 (wrong) to 1.0 (correct, hard, first attempt) |
| **Episode ends** | When fix passes all tests OR after 5 attempts |
| **Difficulty levels** | Easy, Medium, Hard |

---

## 🔄 Environment Loop

```
reset()
  └─→ Gemini API generates a fresh buggy Python function
  └─→ Runs buggy code to capture the error message
  └─→ Returns observation (buggy code + task + error)

step(action)
  └─→ Receives AI's fixed code
  └─→ Executes fix against test cases in sandbox
  └─→ Returns reward + feedback + done flag
```

---

## 📥 Observation Space

What the AI agent **receives** at each step:

| Field | Type | Description |
|---|---|---|
| `task_description` | string | Natural language description of what the function should do |
| `buggy_code` | string | The broken Python function |
| `error_message` | string | Output when buggy code is run against tests |
| `difficulty` | string | `easy`, `medium`, or `hard` |
| `feedback` | string | Result feedback after each attempt |
| `reward` | float | Reward received for this step |
| `done` | bool | Whether the episode has ended |

### Example Observation:
```json
{
  "task_description": "Fix the function so it returns the largest number in a list.",
  "buggy_code": "def find_max(nums):\n    return min(nums)",
  "error_message": "AssertionError\n",
  "difficulty": "medium",
  "feedback": "Fix the bug above.",
  "reward": 0.0,
  "done": false
}
```

---

## 📤 Action Space

What the AI agent **sends** at each step:

| Field | Type | Description |
|---|---|---|
| `fixed_code` | string | The corrected Python function |

### Example Action:
```json
{
  "fixed_code": "def find_max(nums):\n    return max(nums)"
}
```

---

## 🏆 Reward Structure

| Condition | Reward |
|---|---|
| Wrong answer | `0.0` |
| Correct — Easy — 1st attempt | `0.6` |
| Correct — Medium — 1st attempt | `0.8` |
| Correct — Hard — 1st attempt | `1.0` |
| Each additional attempt | `-0.1` penalty |
| Minimum reward (if correct) | `0.1` |

The reward structure encourages the agent to:
- Solve harder problems for greater reward
- Fix bugs in fewer attempts
- Not give up (episode ends at 5 attempts)

---

## ♾️ Dynamic Challenge Generation

Challenges are generated **on the fly** using the **Gemini API** (`gemini-2.0-flash`):

- Every `reset()` call produces a **brand new, unique** buggy function
- Difficulty is randomly selected: `easy`, `medium`, or `hard`
- Bugs include: wrong operators, wrong function calls, wrong return values, off-by-one errors, wrong conditions
- If Gemini is unavailable (rate limit/network), falls back to static challenge pool automatically

### Example Generated Challenges:

**Easy:**
```python
# Bug: uses subtraction instead of addition
def add(a, b):
    return a - b
```

**Medium:**
```python
# Bug: uses [::1] instead of [::-1]
def reverse_string(s):
    return s[::1]
```

**Hard:**
```python
# Bug: fib(n-3) instead of fib(n-2)
def fib(n):
    if n <= 0: return 0
    if n == 1: return 1
    return fib(n-1) + fib(n-3)
```

---

## 🚀 Quick Start

### Install

```bash
pip install git+https://huggingface.co/spaces/yourusername/debug_env
```

### Use (Async)

```python
from debug_env import DebugEnv, DebugAction

async with DebugEnv(base_url="https://yourusername-debug-env.hf.space") as env:
    result = await env.reset()
    obs = result.observation
    print("Task:", obs["task_description"])
    print("Buggy code:", obs["buggy_code"])

    fix = DebugAction(fixed_code="def add(a, b):\n    return a + b")
    result = await env.step(fix)
    print("Reward:", result.reward)
    print("Feedback:", result.observation["feedback"])
```

### Use (Sync)

```python
from debug_env import DebugEnv, DebugAction

with DebugEnv(base_url="https://yourusername-debug-env.hf.space").sync() as env:
    result = env.reset()
    obs = result.observation
    print("Task:", obs["task_description"])

    fix = DebugAction(fixed_code="def find_max(nums):\n    return max(nums)")
    result = env.step(fix)
    print("Reward:", result.reward)
```

---

## 🔁 Full Episode Example

```python
from debug_env import DebugEnv, DebugAction

with DebugEnv(base_url="https://yourusername-debug-env.hf.space").sync() as env:
    result = env.reset()
    obs = result.observation

    print(f"Difficulty: {obs['difficulty']}")
    print(f"Task: {obs['task_description']}")
    print(f"Buggy Code:\n{obs['buggy_code']}")
    print(f"Error: {obs['error_message']}")

    # Agent submits a fix
    result = env.step(DebugAction(fixed_code="def add(a, b):\n    return a + b"))

    print(f"Reward: {result.reward}")
    print(f"Done: {result.observation['done']}")
    print(f"Feedback: {result.observation['feedback']}")
```

Output:
```
Difficulty: easy
Task: Fix the function so it returns the sum of two numbers.
Buggy Code:
def add(a, b):
    return a - b
Error: AssertionError

Reward: 0.6
Done: True
Feedback: All tests passed in 1 attempt(s)!
```

---

## 🛠️ API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/reset` | POST | Start a new episode |
| `/step` | POST | Submit an action |
| `/state` | GET | Get current episode state |
| `/docs` | GET | Swagger UI |
| `/health` | GET | Health check |

---

## 📁 Project Structure

```
debug_env/
├── __init__.py                          # Exports DebugEnv, DebugAction, DebugObservation
├── models.py                            # Action and Observation type definitions
├── client.py                            # DebugEnv client class
├── README.md                            # This file
├── openenv.yaml                         # Environment manifest
├── pyproject.toml                       # Dependencies
└── server/
    ├── debug_env_environment.py         # Core logic: task, grader, reward
    ├── app.py                           # FastAPI app
    ├── requirements.txt                 # Server dependencies
    └── Dockerfile                       # Container definition
```

---

## ⚙️ Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GEMINI_API_KEY` | Recommended | Enables dynamic challenge generation via Gemini API |

Without `GEMINI_API_KEY`, the environment falls back to the static challenge pool automatically.

---

## 🧰 Tech Stack

| Component | Technology |
|---|---|
| Framework | [OpenEnv](https://github.com/meta-pytorch/OpenEnv) by Meta & Hugging Face |
| API | FastAPI + Uvicorn |
| Container | Docker |
| Deployment | Hugging Face Spaces |
| Challenge Generation | Google Gemini API (`gemini-2.0-flash`) |
| Code Execution | Python `subprocess` (sandboxed, 5s timeout) |
| Data Validation | Pydantic |

---

## 🔒 Safety

- All submitted code runs in a **subprocess** with a **5 second timeout**
- Code execution is isolated — cannot affect the server
- Malicious or infinite loop code is automatically killed

---

## 📊 Use Cases for RL Training

This environment is ideal for training LLMs to:
- Understand and reason about code
- Identify logical bugs
- Generate correct code fixes
- Improve with feedback over multiple attempts

Compatible with: **TRL (GRPO)**, **torchforge**, **SkyRL**, **Unsloth**, **ART**, **Oumi**

