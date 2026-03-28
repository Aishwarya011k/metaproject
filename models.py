from openenv.core import Observation, Action

class DebugAction(Action):
    fixed_code: str

class DebugObservation(Observation):
    buggy_code: str
    error_message: str
    task_description: str
    difficulty: str
    feedback: str
    reward: float = 0.0
    done: bool = False