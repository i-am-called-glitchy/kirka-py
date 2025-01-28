from typing import Dict, Any
from models.user import UserProfile

class CommandContext:
    def __init__(self, message: dict, bot):
        print(message)
        self.bot = bot
        self.message = message['content']
        self.content = self.message
        self.author = self._create_author(message['author'])
        self.command_name = self._parse_command_name()
        self.args = self._parse_args()

    def _create_author(self, author_data: dict):
        return type('Author', (), {
            'id': author_data.get('id', ''),
            'short_id': author_data.get('short_id', ''),
            'name': author_data.get('name', ''),
            'role': author_data.get('role', ''),
            'level': author_data.get('level', 0)
        })

    def _parse_command_name(self):
        if not self.content.startswith(self.bot.prefix):
            return ''
        parts = self.content[len(self.bot.prefix):].split()
        return parts[0].lower() if parts else ''

    def _parse_args(self):
        if not self.content.startswith(self.bot.prefix):
            return []
        parts = self.content[len(self.bot.prefix):].split()
        return parts[1:] if len(parts) > 1 else []

    async def reply(self, response: str, raw=False):
        if not raw:
            response = f"{self.author.short_id} -|- {response}"
        await self.bot.api.send_global_chat(response)
        print(response)


