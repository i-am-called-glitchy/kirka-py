from datetime import datetime
from typing import Dict, Optional


class UserProfile:
    def __init__(self, raw_data: Dict):
        self.raw = raw_data
        self.stats = raw_data.get('stats', {})

    @property
    def id(self) -> str:
        return self.raw['id']

    @property
    def short_id(self) -> str:
        return self.raw['shortId']

    @property
    def name(self) -> str:
        return self.raw['name']

    @property
    def bio(self) -> str:
        return self.raw.get('bio', 'No bio')

    @property
    def role(self) -> str:
        return self.raw['role']

    @property
    def level(self) -> int:
        return self.raw['level']

    @property
    def total_xp(self) -> int:
        return self.raw['totalXp']

    @property
    def xp_progress(self) -> str:
        current = self.raw['xpSinceLastLevel']
        needed = self.raw['xpUntilNextLevel']
        return f"{current}/{needed} ({current / needed:.1%})"

    @property
    def coins(self) -> int:
        return self.raw['coins']

    @property
    def diamonds(self) -> int:
        return self.raw['diamonds']

    @property
    def join_date(self) -> str:
        return datetime.strptime(
            self.raw['createdAt'],
            '%Y-%m-%dT%H:%M:%S.%fZ'
        ).strftime('%B %d, %Y')

    @property
    def clan(self) -> Optional[str]:
        return self.raw.get('clan')

    @property
    def weapon_skin(self) -> str:
        skin = self.raw['activeWeapon1Skin']
        return f"{skin['name']} ({skin['rarity']})"

    @property
    def body_skin(self) -> str:
        skin = self.raw['activeBodySkin']
        return f"{skin['name']} ({skin['rarity']})"

    @property
    def kd_ratio(self) -> float:
        return self.stats.get('kills', 1) / self.stats.get('deaths', 1)

    @property
    def win_rate(self) -> float:
        return self.stats.get('wins', 0) / self.stats.get('games', 1)

    @property
    def headshot_rate(self) -> float:
        return self.stats.get('headshots', 0) / self.stats.get('kills', 1)

    @property
    def score_per_game(self) -> float:
        return self.stats.get('scores', 0) / self.stats.get('games', 1)