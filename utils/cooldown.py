from expiringdict import ExpiringDict
import time

class CooldownController:
    def __init__(self):
        self.cooldowns = ExpiringDict(max_len=100, max_age_seconds=5)

    def check(self, user_id: str, command: str) -> bool:
        key = f"{user_id}:{command}"
        return key in self.cooldowns

    def remaining(self, user_id: str, command: str) -> int:
        key = f"{user_id}:{command}"
        return self.cooldowns[key] - time.time()

    def update(self, user_id: str, command: str):
        key = f"{user_id}:{command}"
        self.cooldowns[key] = time.time() + self.cooldowns.max_age