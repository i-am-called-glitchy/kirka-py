import aiohttp
import websockets
import asyncio
import json
import logging
import traceback
from functools import lru_cache
import re

# Set up logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def log_errors(func):
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            method_name = func.__name__
            logger.error(f"Error in {method_name}: {str(e)}")
            error_trace = traceback.format_exc()
            logger.error(error_trace)
            return {"error": str(e)}  # Return error as a dictionary
    return decorator

class KirkaAPI:
    def __init__(self, url=None, rawchaturl=None, token=""):
        self.url = url if url else "kirka.io"
        self.rawchaturl = f"wss://chat.{self.url}/" if not rawchaturl else rawchaturl
        self.token = token
        self.websocket = None
        self.session = None

    async def initialize(self):
        """Initialize the API connection"""
        self.session = aiohttp.ClientSession()
        await self._connect_websocket()

    @log_errors
    async def _connect_websocket(self):
        """Establish WebSocket connection"""
        try:
            self.websocket = await websockets.connect(
                self.rawchaturl,
                subprotocols=[self.token] if self.token else None
            )
            print("WebSocket connection established.")
            await self._listen()
        except Exception as e:
            print(f"WebSocket connection failed: {str(e)}")
            raise

    async def _listen(self):
        """Listen for incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    message_dict = json.loads(message)
                    await self._process_message(message_dict)
                except json.JSONDecodeError as e:
                    print(f"Failed to parse message: {str(e)}")
        except websockets.exceptions.ConnectionClosed:
            print("WebSocket connection closed")
        except Exception as e:
            print(f"Error in message listening: {str(e)}")

    async def _process_message(self, message):
        """Process incoming messages and trigger appropriate handlers"""
        try:
            # General message handler
            if hasattr(self, 'on_message'):
                await self.on_message(message)

            # Only process if message is of type 13 and has no user
            if message.get("type") == 13 and message.get("user") is None:
                message_content = message.get("message", "")

                # Trade message handler
                if hasattr(self, 'trade_message'):
                    await self.trade_message(message)

                # Trade send handler
                if hasattr(self, 'trade_send') and "is offering their" in message_content:
                    await self.trade_send(message)

                # Trade accepted handler
                if hasattr(self, 'trade_accepted') and "** accepted **" in message_content and "**'s offer" in message_content:
                    await self.trade_accepted(message)

                # Trade cancel handler
                if hasattr(self, 'trade_cancel') and "cancelled their trade" in message_content:
                    await self.trade_cancel(message)

        except Exception as e:
            print(f"Error processing message: {str(e)}")

    @log_errors
    async def send_global_chat(self, message):
        """Send a message to global chat"""
        if self.websocket:
            try:
                await self.websocket.send(message)
                return "POSTED MESSAGE"
            except Exception as e:
                return f"Failed to send message: {str(e)}"
        return "WebSocket is not open or not connected."

    @log_errors
    async def close(self):
        """Close all connections"""
        try:
            if self.websocket:
                await self.websocket.close()
            if self.session:
                await self.session.close()
        except Exception as e:
            print(f"Error closing connections: {str(e)}")

    # User-related methods
    @log_errors
    async def get_stats(self, short_id):
        short_id = short_id.upper().replace("#", "")
        url = f"https://api.{self.url}/api/user/getProfile"
        payload = {"id": short_id, "isShortId": True}
        async with self.session.post(url, json=payload) as response:
            return await response.json()

    @log_errors
    async def get_stats_long_id(self, long_id):
            url = f"https://api.{self.url}/api/user/getProfile"
            payload = {"id": long_id}
            async with self.session.post(url, json=payload) as response:
                return await response.json()

    @log_errors
    async def get_my_profile(self, token):
            url = f"https://api.{self.url}/api/user"
            headers = {"Authorization": f"Bearer {token}"}
            async with self.session.get(url, headers=headers) as response:
                return await response.json()

    @log_errors
    async def send_friend_request(self, token, short_id):
            short_id = short_id.upper().replace("#", "")
            url = f"https://api.{self.url}/api/user/offerFriendship"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"shortId": short_id}
            async with self.session.post(url, headers=headers, json=payload) as response:
                try:
                    return await response.json()
                except:
                    return response.status

    @log_errors
    async def accept_friend_request(self, token, long_id):
            url = f"https://api.{self.url}/api/user/acceptFriendship"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"userId": long_id}
            async with self.session.post(url, headers=headers, json=payload) as response:
                try:
                    return await response.json()
                except:
                    return response.status

    @log_errors
    async def decline_friend_request(self, token, long_id):
            url = f"https://api.{self.url}/api/user/cancelFriendship"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"userId": long_id}
            async with self.session.post(url, headers=headers, json=payload) as response:
                try:
                    return await response.json()
                except:
                    return response.status

    @log_errors
    async def remove_friend(self, token, long_id):
            url = f"https://api.{self.url}/api/user/cancelFriendship"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"userId": long_id}
            async with self.session.post(url, headers=headers, json=payload) as response:
                try:
                    return await response.json()
                except:
                    return response.status
    @log_errors
    async def rename(self, token, name):
            url = f"https://api.{self.url}/api/user/updateProfile"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"name": name}
            async with self.session.post(url, headers=headers, json=payload) as response:
                return await response.json()

    # Inventory-related methods
    @log_errors
    async def get_inventory(self, api_key, long_id):
            url = f"https://api.{self.url}/api/inventory/get_{api_key}"
            payload = {"id": long_id}
            async with self.session.post(url, json=payload) as response:
                return await response.json()

    @log_errors
    async def get_my_inventory(self, token):
            url = f"https://api.{self.url}/api/inventory"
            headers = {"Authorization": f"Bearer {token}"}
            async with self.session.get(url, headers=headers) as response:
                return await response.json()

    @log_errors
    async def open_chest(self, token, item_id):
            url = f"https://api.{self.url}/api/inventory/openChest"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"id": item_id}
            async with self.session.post(url, headers=headers, json=payload) as response:
                return await response.json()
    @log_errors
    async def open_golden_chest(self, token):
        return await self.open_chest(token, "077a4cf2-7b76-4624-8be6-4a7316cf5906")

    @log_errors
    async def open_ice_chest(self, token):
        return await self.open_chest(token, "ec230bdb-4b96-42c3-8bd0-65d204a153fc")

    @log_errors
    async def open_wood_chest(self, token):
        return await self.open_chest(token, "71182187-109c-40c9-94f6-22dbb60d70ee")

    @log_errors
    async def open_character_card(self, token, item_id):
            url = f"https://api.{self.url}/api/inventory/openCharacterCard"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"id": item_id}
            async with self.session.post(url, headers=headers, json=payload) as response:
                return await response.json()

    @log_errors
    async def open_cold_character_card(self, token):
        return await self.open_character_card(token, "723c4ba7-57b3-4ae4-b65e-75686fa77bf2")

    @log_errors
    async def open_girls_band_character_card(self, token):
        return await self.open_character_card(token, "723c4ba7-57b3-4ae4-b65e-75686fa77bf1")

    @log_errors
    async def open_party_character_card(self, token):
        return await self.open_character_card(token, "6281ed5a-663a-45e1-9772-962c95aa4605")

    @log_errors
    async def open_soldiers_character_card(self, token):
        return await self.open_character_card(token, "9cc5bd60-806f-4818-a7d4-1ba9b32bd96c")

    @log_errors
    async def equip_item(self, token, item_id):
            url = f"https://api.{self.url}/api/inventory/take"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"id": item_id}
            async with self.session.post(url, headers=headers, json=payload) as response:
                try:
                    return await response.json()
                except:
                    return response.status
    @log_errors
    async def list_item(self, token, item_id, price):
            url = f"https://api.{self.url}/api/inventory/market"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"id": item_id, "price": price}
            async with self.session.post(url, headers=headers, json=payload) as response:
                try:
                    return await response.json()
                except:
                    return response.status

    @log_errors
    async def quick_sell(self, token, item_id, amount):
            url = f"https://api.{self.url}/api/inventory/sell"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"id": item_id, "amount": amount}
            async with self.session.post(url, headers=headers, json=payload) as response:
                try:
                    return await response.json()
                except:
                    return response.status

    async def quick_sell_one(self, token, item_id):
        return await self.quick_sell(token, item_id, 1)

    # Market-related methods
    @log_errors
    async def get_market(self, token):
            url = f"https://api.{self.url}/api/market"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"search": "", "rarity": ""}
            async with self.session.post(url, headers=headers, json=payload) as response:
                return await response.json()

    @log_errors
    async def search_market(self, token, skin=None, rarity=None):
            url = f"https://api.{self.url}/api/market"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"search": skin or "", "rarity": rarity or ""}
            async with self.session.post(url, headers=headers, json=payload) as response:
                return await response.json()

    @log_errors
    async def market_buy(self, token, long_id, item_id):
            url = f"https://api.{self.url}/api/market/buy"
            headers = {"Authorization": f"Bearer {token}"}
            payload = {"userId": long_id, "itemId": item_id}
            async with self.session.post(url, headers=headers, json=payload) as response:
                try:
                    return await response.json()
                except:
                    return response.status

    # Rewards-related methods
    @log_errors
    async def get_rewards(self, token):
            url = f"https://api.{self.url}/api/rewards"
            headers = {"Authorization": f"Bearer {token}"}
            async with self.session.get(url, headers=headers) as response:
                return await response.json()


    @log_errors
    async def get_ads(self, token):
        url = f"https://api.{self.url}/api/rewards/ad"
        headers = {"Authorization": f"Bearer {token}"}
        async with self.session.post(url, headers=headers) as response:
            return await response.json()

    @log_errors
    async def get_ad_reward(self):
        url = f"https://api.{self.url}/api/rewards/ad"
        async with self.session.get(url) as response:
            return await response.json()

    @log_errors
    async def claim_rewards(self, token):
        url = f"https://api.{self.url}/api/rewards/take"
        headers = {"Authorization": f"Bearer {token}"}
        async with self.session.post(url, headers=headers) as response:
            return await response.json()

    @log_errors
    async def claim_ad(self, token):
        url = f"https://api.{self.url}/api/rewards/claimAd"
        headers = {"Authorization": f"Bearer {token}"}
        async with self.session.get(url, headers=headers) as response:
            return await response.json()

    # Clans-related methods
    @log_errors
    async def get_clan(self, name):
        url = f"https://api.{self.url}/api/clans/{name}"
        async with self.session.get(url) as response:
            return await response.json()
    @log_errors
    async def invite_clan(self, token, short_id):
        url = f"https://api.{self.url}/api/clans/invite"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"shortId": short_id}
        async with self.session.post(url, headers=headers, json=payload) as response:
            try:
                return await response.json()
            except:
                return response.status

    async def get_my_clan(self, token):
        url = f"https://api.{self.url}/api/clans/mine"
        headers = {"Authorization": f"Bearer {token}"}
        async with self.session.get(url, headers=headers) as response:
            return await response.json()

    @log_errors
    async def update_clan_description(self, token, clan_id, description):
        url = f"https://api.{self.url}/api/clans/updateClan"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"id": clan_id, "description": description}
        async with self.session.post(url, headers=headers, json=payload) as response:
            return await response.json()

    @log_errors
    async def update_clan_discord_link(self, token, clan_id, discord_link):
        url = f"https://api.{self.url}/api/clans/updateClan"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"id": clan_id, "discordLink": discord_link}
        async with self.session.post(url, headers=headers, json=payload) as response:
            return await response.json()

    @log_errors
    async def accept_invite(self, token, invite_id):
        url = f"https://api.{self.url}/api/clans/acceptInvite"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"inviteId": invite_id}
        async with self.session.post(url, headers=headers, json=payload) as response:
            try:
                return await response.json()
            except:
                return response.status

    @log_errors
    async def decline_invite(self, token, invite_id):
        url = f"https://api.{self.url}/api/clans/cancelInvite"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"inviteId": invite_id}
        async with self.session.post(url, headers=headers, json=payload) as response:
            try:
                return await response.json()
            except:
                return response.status

    @log_errors
    async def leave_clan(self, token):
        url = f"https://api.{self.url}/api/clans/leave"
        headers = {"Authorization": f"Bearer {token}"}
        async with self.session.post(url, headers=headers) as response:
            try:
                return await response.json()
            except:
                return response.status

    @log_errors
    async def set_role(self, token, long_id, role):
        url = f"https://api.{self.url}/api/clans/updateMember"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"memberId": long_id, "role": role}
        async with self.session.post(url, headers=headers, json=payload) as response:
            try:
                return await response.json()
            except:
                return response.status

    @log_errors
    async def set_officer(self, token, long_id):
        return await self.set_role(token, long_id, "OFFICER")

    @log_errors
    async def set_newbie(self, token, long_id):
        return await self.set_role(token, long_id, "NEWBIE")

    @log_errors
    async def set_leader(self, token, long_id):
        return await self.set_role(token, long_id, "LEADER")

    @log_errors
    async def clan_kick(self, token, long_id):
        url = f"https://api.{self.url}/api/clans/kickMember"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"memberId": long_id}
        async with self.session.post(url, headers=headers, json=payload) as response:
            try:
                return await response.json()
            except:
                return response.status

    @log_errors
    async def create_clan(self, token, name):
        url = f"https://api.{self.url}/api/clans/create"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"name": name}
        async with self.session.post(url, headers=headers, json=payload) as response:
            return await response.json()

    # Notification-related methods
    @log_errors
    async def get_notification(self, token):
        url = f"https://api.{self.url}/api/notification"
        headers = {"Authorization": f"Bearer {token}"}
        async with self.session.get(url, headers=headers) as response:
            return await response.json()

    @log_errors
    async def saw_notification(self, token):
        url = f"https://api.{self.url}/api/notification/saw"
        headers = {"Authorization": f"Bearer {token}"}
        async with self.session.get(url, headers=headers) as response:
            try:
                return await response.json()
            except:
                return response.status

    # Leaderboard-related methods
    @log_errors
    async def get_solo_leaderboard(self):
        url = f"https://api.{self.url}/api/leaderboard/solo"
        async with self.session.get(url) as response:
            return await response.json()

    @log_errors
    async def get_clan_leaderboard(self):
        url = f"https://api.{self.url}/api/leaderboard/clanChampionship"
        async with self.session.get(url) as response:
            return await response.json()

    # Shop-related methods
    @log_errors
    async def get_sets(self):
        url = f"https://api.{self.url}/api/shop/sets"
        async with self.session.get(url) as response:
            return await response.json()

    @log_errors
    async def get_bundles(self):
        url = f"https://api.{self.url}/api/shop/bundles"
        async with self.session.get(url) as response:
            return await response.json()

    @log_errors
    async def store_buy(self, token, item_id):
        url = f"https://api.{self.url}/api/shop/buy"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"id": item_id}
        async with self.session.post(url, headers=headers, json=payload) as response:
            return await response.json()

    @log_errors
    async def store_buy_set(self, token, set_id):
        url = f"https://api.{self.url}/api/shop/buySet"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"id": set_id}
        async with self.session.post(url, headers=headers, json=payload) as response:
            return await response.json()

    @log_errors
    async def buy_wood(self, token):
        return await self.store_buy(token, 1)

    @log_errors
    async def buy_ice(self, token):
        return await self.store_buy(token, 2)

    @log_errors
    async def buy_golden(self, token):
        return await self.store_buy(token, 3)

    @log_errors
    async def buy_party(self, token):
        return await self.store_buy(token, 4)

    @log_errors
    async def buy_soldiers(self, token):
        return await self.store_buy(token, 5)

    @log_errors
    async def buy_girls_band(self, token):
        return await self.store_buy(token, 6)

    @log_errors
    async def buy_cold(self, token):
        return await self.store_buy(token, 30)

    # Quests-related methods
    @log_errors
    async def get_all_quests(self, token):
        url = f"https://api.{self.url}/api/quests"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {}
        async with self.session.post(url, headers=headers, json=payload) as response:
            return await response.json()

    @log_errors
    async def get_daily_quests(self, token):
        url = f"https://api.{self.url}/api/quests"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"type": "daily"}
        async with self.session.post(url, headers=headers, json=payload) as response:
            return await response.json()

    @log_errors
    async def get_event_quests(self, token):
        url = f"https://api.{self.url}/api/quests"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"type": "event"}
        async with self.session.post(url, headers=headers, json=payload) as response:
            return await response.json()

    @log_errors
    async def get_hourly_quests(self, token):
        url = f"https://api.{self.url}/api/quests"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"type": "hourly"}
        async with self.session.post(url, headers=headers, json=payload) as response:
            return await response.json()

    @log_errors
    async def get_quests(self, token, quest_type):
        url = f"https://api.{self.url}/api/quests"
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"type": quest_type}
        async with self.session.post(url, headers=headers, json=payload) as response:
            return await response.json()

    # Content-related methods
    @log_errors
    async def get_videos(self):
        url = f"https://api.{self.url}/api/videos"
        async with self.session.post(url) as response:
            return await response.json()

    @log_errors
    async def get_streams(self):
        url = f"https://api.{self.url}/api/twitch"
        async with self.session.get(url) as response:
            return await response.json()

    # Matchmaker-related methods
    @log_errors
    async def get_lobbies(self, region):
        url = f"https://{region}.{self.url}/matchmake/"
        async with self.session.get(url) as response:
            return await response.json()

    @log_errors
    async def get_eu_lobbies(self):
        return await self.get_lobbies("eu1")

    @log_errors
    async def get_na_lobbies(self):
        return await self.get_lobbies("na1")

    @log_errors
    async def get_sa_lobbies(self):
        return await self.get_lobbies("sa1")

    @log_errors
    async def get_asia_lobbies(self):
        return await self.get_lobbies("asia1")

    @log_errors
    async def get_oce_lobbies(self):
        return await self.get_lobbies("oceania1")

    @log_errors
    async def get_staging_lobbies(self):
        return await self.get_lobbies("staging-na")

    @log_errors
    async def get_playercount(self, region):
        url = f"https://{region}.{self.url}/matchmake/"
        try:
            async with self.session.get(url) as response:
                data = await response.json()
                return sum(lobby["clients"] for lobby in data)
        except:
            return 0

    @log_errors
    async def get_eu_playercount(self):
        return await self.get_playercount("eu1")

    @log_errors
    async def get_na_playercount(self):
        return await self.get_playercount("na1")

    @log_errors
    async def get_sa_playercount(self):
        return await self.get_playercount("sa1")

    @log_errors
    async def get_asia_playercount(self):
        return await self.get_playercount("asia1")

    @log_errors
    async def get_oce_playercount(self):
        return await self.get_playercount("oceania1")

    @log_errors
    async def get_staging_playercount(self):
        return await self.get_playercount("staging-na")

    # No API fetches
    async def get_character_render(self, skin_name):
        # TODO: steal carry's code
        raise NotImplementedError

    async def get_level_rewards(self):
        # TODO: steal carry's code
        raise NotImplementedError

    @lru_cache(maxsize=None)
    async def pricebvl(self, skinname):
        try:
            async with self.session.get(
                    "https://opensheet.elk.sh/1tzHjKpu2gYlHoCePjp6bFbKBGvZpwDjiRzT9ZUfNwbY/Alphabetical") as response:
                data = await response.json()

            skinname = skinname.lower()
            for item in data:
                if item.get("Skin Name") and item.get("Price"):
                    if item["Skin Name"].lower() == skinname:
                        price_str = item["Price"].split()[0].split("?")[0]
                        return int(re.sub(r'[,./]', '', price_str))
            return 0
        except Exception as e:
            return str(e)

    @log_errors
    @lru_cache(maxsize=None)
    async def priceyzzzmtz(self, skinname):
        try:
            async with self.session.get(
                    "https://opensheet.elk.sh/1VqX9kwJx0WlHWKCJNGyIQe33APdUSXz0hEFk6x2-3bU/Sorted+View") as response:
                data = await response.json()

            skinname = skinname.lower()
            for item in data:
                if item.get("Name") and item.get("Base Value"):
                    if item["Name"].lower() == skinname:
                        price_str = item["Base Value"].split()[0].split("?")[0]
                        return int(re.sub(r'[,./]', '', price_str))
            return 0
        except Exception as e:
            return str(e)
    @log_errors
    @lru_cache(maxsize=None)
    async def pricecustom(self, skinname, namefield, pricefield, opensheeturl):
        try:
            async with self.session.get(opensheeturl) as response:
                data = await response.json()

            skinname = skinname.lower()
            for item in data:
                if item.get(namefield) and item.get(pricefield):
                    if item[namefield].lower() == skinname:
                        price_str = item[pricefield].split()[0].split("?")[0]
                        return int(re.sub(r'[,./]', '', price_str))
            return 0
        except Exception as e:
            return str(e)

    async def inventory_value_bvl(self, inventory):
        # TODO: steal carry's code, this is useful only if you have an api key and i cant test it because idont
        raise NotImplementedError

    async def inventory_value_yzzzmtz(self, inventory):
        # TODO: steal carry's code, this is useful only if you have an api key and i cant test it because idont
        raise NotImplementedError

    async def inventory_value_custom(self, inventory, name_field, price_field, opensheet_url):
        # TODO: steal carry's code, this is useful only if you have an api key and i cant test it because idont
        raise NotImplementedError

    # Error code translation
    async def request_error_code_translate(self, request_code):
        error_codes = {
            101: "User is already your friend",
            102: "User not found",
            103: "User cannot change name",
            104: "Already sent friend request",
            105: "User hasn't sent you a friend request",
            106: "User already sent you a friend request",
            107: "You do not have shared connections with this user",
            108: "You don't have enough coins",
            109: "You cannot buy your own item",
            110: "Your profile cannot contain bad words",
            201: "Item is not in the user's inventory",
            202: "Item already selected",
            203: "Item not selectable",
            204: "Item cannot be sold",
            205: "Item cannot be opened",
            206: "User doesn't have this amount of the item",
            207: "Item is locked. Reason: trade offer",
            301: "Item not found",
            302: "Leader positions error",
            303: "Item ID should exist",
            401: "Clan name already taken",
            402: "You can create only one clan",
            403: "Clan not found",
            404: "User already invited to the clan",
            405: "User is in this clan",
            406: "User already belongs to another clan",
            407: "User is not a clan member",
            408: "Invite not found or not related to the user",
            409: "Your clan name cannot contain bad words",
            501: "Shop element not found",
            502: "Not enough money",
            503: "Item already purchased",
            504: "You can already change your name",
            601: "This item isn't for sale anymore",
            602: "You need level 10 to use the market",
            801: "You have not linked your Twitch account",
            802: "Token expired, re-connect your Twitch account",
            9901: "Database error",
            9902: "You do not have permission for this",
            9903: "Cannot do it to yourself",
            9904: "Exceeded length limit",
            9905: "Notification not found or not related to the user",
            9906: "Something went wrong",
            9907: "Small level for this action",
            9908: "Your friend exceeds the friends limit",
            9909: "Exceeded limit of friend requests per day",
            9910: "Rate limit exceeded",
            9911: "Service temporarily unavailable",
        }
        return error_codes.get(request_code, "Unknown error")

    # Forbidden resources
    async def get_shop(self, token):
        url = f"https://api.{self.url}/api/shop"
        headers = {"Authorization": f"Bearer {token}"}
        async with self.session.get(url, headers=headers) as response:
            return await response.json()

    async def reports(self, token):
        url = f"https://api.{self.url}/api/inspector/reports"
        headers = {"Authorization": f"Bearer {token}"}
        async with self.session.post(url, headers=headers) as response:
            return await response.json()

    # Cleanup
    async def close(self):
        await self.session.close()
