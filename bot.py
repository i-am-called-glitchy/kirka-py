import asyncio
import aiohttp
from expiringdict import ExpiringDict
from typing import Dict, Optional, Callable
from models.ctx import CommandContext
from api.client import KirkaAPI
from utils.cooldown import CooldownController
from utils.response import CommandResponse
import traceback, sys

# noinspection PyUnresolvedReferences
class KirkaBot:
    def __init__(self, prefix: str = ".", token: Optional[str] = None):
        self.prefix = prefix
        self.token = token
        self.commands: Dict[str, Callable] = {}  # Stores command functions
        self.api = KirkaAPI(token=token)
        self.cooldowns = CooldownController()
        self.api._process_message = self.handle_message
        self.blacklists = {
            'silent': set(),
            'notified': set(),
            'command': ExpiringDict(max_len=1000, max_age_seconds=3600)
        }
        self.discarded_first_message = False

    def command(self, name: str = None, description: str = "", aliases: list = None, hidden: bool = False):
        # noinspection PyTypeChecker
        def decorator(func: Callable):
            cmd_name = name or func.__name__
            cmd_info = {
                'function': func,
                'description': description,
                'aliases': aliases or [],
                'hidden': hidden
            }
            self.commands[cmd_name] = cmd_info
            for alias in cmd_info['aliases']:
                self.commands[alias] = cmd_info
            return func
        return decorator

    async def _init_session(self):
        # Initialize aiohttp ClientSession
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        # Close the aiohttp session
        if self.session:
            await self.session.close()

    async def handle_message(self, message: dict):
        if not self.session:
            await self._init_session()

        # Ignore the first message
        if not self.discarded_first_message:
            self.discarded_first_message = True
            return

        try:
            msg_type = message.get('type')

            if msg_type == 3:  # Bundle of messages
                if 'messages' in message:
                    for bundled_msg in message['messages']:
                        await self._process_single_message(bundled_msg)
            elif msg_type == 2:  # Single message
                await self._process_single_message(message)
            else:  # Unknown type
                try:
                    await self._process_single_message(message)
                except Exception as e:
                    print(f"Failed to process message of unknown type {msg_type}:")
                    traceback.print_exc()
                    return

        except Exception as e:
            print("Error in handle_message:")
            traceback.print_exc()

    async def _process_single_message(self, message: dict):
        try:
            # Create normalized message structure
            normalized_message = {
                'content': message.get('message', ''),
                'author': {
                    'id': message['user'].get('id', ''),
                    'short_id': message['user'].get('shortId', ''),
                    'name': message['user'].get('name', ''),
                    'role': message['user'].get('role', ''),
                    'level': message['user'].get('level', 0)
                },
                'type': message.get('type'),
                'raw': message
            }

            # Create context and check if it's a command
            ctx = self.create_context(normalized_message)

            if not ctx.content.startswith(self.prefix):
                return

            user_id = ctx.author.short_id
            getblacklist = self._check_blacklists(user_id, ctx.command_name)

            if getblacklist == 1:
                return

            if ctx.command_name in self.commands:
                if getblacklist == 2:
                    await ctx.reply("Blacklisted")
                elif getblacklist == 3:
                    await ctx.reply("Blacklisted from using this command.")
                else:
                    await self._execute_command(ctx)

        except Exception as e:
            print("Error in _process_single_message:")
            traceback.print_exc()
            raise

    async def _execute_command(self, ctx):
        cmd_name = ctx.command_name
        if cmd_name not in self.commands:
            await ctx.reply("Command not found.")
            return

        command = self.commands[cmd_name]
        try:
            if self.cooldowns.check(ctx.author.id, cmd_name):
                remaining = self.cooldowns.remaining(ctx.author.id, cmd_name)
                await ctx.reply(f"Command on cooldown. Wait {round(remaining,2)}s")
                return

            # Get the message content and remove the prefix + command name
            args = ctx.content[len(self.prefix + cmd_name):].strip()

            await command['function'](ctx, args)
            self.cooldowns.update(ctx.author.id, cmd_name)

        except Exception as e:
            print("Error in _execute_command:")
            traceback.print_exc()
            error_response = CommandResponse().add_error(f"{str(e)}\n```\n{traceback.format_exc()}```")
            await ctx.reply(error_response.build())

    def create_context(self, message: dict):
        return CommandContext(message, self)

    def _check_blacklists(self, user_id: str, command_name: str):
        if user_id in self.blacklists['silent']:
            return 1
        if user_id in self.blacklists['notified']:
            return 2
        if user_id in self.blacklists['command'].get(command_name, set()):
            return 3
        return False

    async def start(self):
        try:
            await self._init_session()
            await self.api.initialize()
            print("Bot is ready!")
            await asyncio.Event().wait() # hang so that bot dosent exit out
        except asyncio.CancelledError:
            print("Bot is shutting down.")
            await self.close_session()
        except Exception as e:
            print(f"An error occurred: {e}")
            await self.close_session()
            raise e

    @staticmethod
    async def _setup_bot(bot):
        await bot.start()

if __name__ == "__main__":
    bot = KirkaBot(token="testbot")
    bot.api.rawchaturl = "ws://localhost:8765" # test server

    asyncio.run(bot.start())