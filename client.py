from openenv.core import EnvClient
from debug_env.models import DebugAction, DebugObservation

class DebugEnv(EnvClient):
    action_type = DebugAction
    observation_type = DebugObservation