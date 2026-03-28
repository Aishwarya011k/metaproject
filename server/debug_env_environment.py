import subprocess
import random
import json
import urllib.request
import os
from openenv.core import Environment
from debug_env.models import DebugAction, DebugObservation

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

def generate_challenge(difficulty: str) -> dict:
    prompt = f"""Generate a Python debugging challenge of {difficulty} difficulty.
Return ONLY a JSON object with exactly these fields, no markdown, no explanation:
{{
    "description": "Fix the function so it ...",
    "buggy_code": "def function_name(...):\\n    ...",
    "test_code": "assert function_name(...) == ...\\nassert function_name(...) == ...\\nprint('PASS')"
}}
Rules:
- The buggy code must have exactly ONE bug
- The test_code must end with print('PASS')
- Return only raw JSON, nothing else"""

    data = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7}
    }).encode()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read())
        text = result["candidates"][0]["content"]["parts"][0]["text"]
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)


FALLBACK_CHALLENGES = [
    {
        "difficulty": "easy",
        "description": "Fix the function so it returns the sum of two numbers.",
        "buggy_code": "def add(a, b):\n    return a - b",
        "test_code": "assert add(2, 3) == 5\nassert add(10, 5) == 15\nprint('PASS')"
    },
    {
        "difficulty": "medium",
        "description": "Fix the function so it reverses a string correctly.",
        "buggy_code": "def reverse_string(s):\n    return s[::1]",
        "test_code": "assert reverse_string('hello') == 'olleh'\nassert reverse_string('abc') == 'cba'\nprint('PASS')"
    },
    {
        "difficulty": "hard",
        "description": "Fix the function so it returns the nth Fibonacci number.",
        "buggy_code": "def fib(n):\n    if n <= 0:\n        return 0\n    if n == 1:\n        return 1\n    return fib(n-1) + fib(n-3)",
        "test_code": "assert fib(1) == 1\nassert fib(5) == 5\nassert fib(10) == 55\nprint('PASS')"
    },
]

class DebugEnvironment(Environment):

    def reset(self, **kwargs):
        self.attempts = 0
        difficulty = random.choice(["easy", "medium", "hard"])

        try:
            self.challenge = generate_challenge(difficulty)
            self.challenge["difficulty"] = difficulty
        except Exception as e:
            print(f"LLM generation failed: {e}, using fallback")
            self.challenge = random.choice(FALLBACK_CHALLENGES)

        error = self._run_code(
            self.challenge["buggy_code"] + "\n" + self.challenge["test_code"]
        )

        return DebugObservation(
            buggy_code=self.challenge["buggy_code"],
            error_message=error,
            task_description=self.challenge["description"],
            difficulty=self.challenge["difficulty"],
            feedback="Fix the bug above.",
            reward=0.0,
            done=False
        )

    def step(self, action: DebugAction, **kwargs):
        self.attempts += 1
        full_code = action.fixed_code + "\n" + self.challenge["test_code"]
        result = self._run_code(full_code)
        passed = "PASS" in result

        if passed:
            base = {"easy": 0.6, "medium": 0.8, "hard": 1.0}
            reward = max(0.1, base[self.challenge["difficulty"]] - (self.attempts - 1) * 0.1)
            feedback = f"All tests passed in {self.attempts} attempt(s)!"
        else:
            reward = 0.0
            feedback = f"Tests failed. Error: {result[:200]}"

        done = passed or self.attempts >= 5

        return DebugObservation(
            buggy_code=self.challenge["buggy_code"],
            error_message=result,
            task_description=self.challenge["description"],
            difficulty=self.challenge["difficulty"],
            feedback=feedback,
            reward=reward,
            done=done
        )

    def state(self, **kwargs):
        return {
            "attempts": self.attempts,
            "difficulty": self.challenge["difficulty"]
        }

    def _run_code(self, code: str) -> str:
        try:
            result = subprocess.run(
                ["python", "-c", code],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout + result.stderr
        except subprocess.TimeoutExpired:
            return "Error: Code timed out"
        except Exception as e:
            return f"Error: {str(e)}"