import logging

import aiohttp
import requests

from config_reader import config

url = config.API_URL

logger = logging.getLogger("API")


class APIError(Exception):
    pass


class API:
    def __init__(self):
        self.url = config.API_URL

    async def request(self, method, endpoint, token=None, **kwargs):
        async with method(
                self.url + endpoint,
                # headers=self.get_default_headers(token or self.token),
                **kwargs,
        ) as resp:
            logger.debug(f"API {endpoint!r} {kwargs} response status {resp.status}")
            if not resp.ok:
                try:
                    error = await resp.json()
                except aiohttp.ContentTypeError:
                    error = await resp.text()
                logger.error(str(error).replace('<', r'\<'))
                raise APIError(error)
            data = await resp.json()
            if isinstance(data, dict) and not data.get("ok", True):
                raise APIError(data)
        return data

    async def get_active_games(self, session, player_id: int):
        result = await self.request(
            session.get, 'active_games',
            json={
                "player_id": player_id,
            },
        )
        return result  # {"ok": true, "codes": [123, 4213, 3]}

    async def get_player_cards(self, session, player_id: int | None = None):
        result = await self.request(
            session.get, 'get_player_cards',
            json={
                "player_id": player_id,
            },
        )
        return result

    async def add_card(self, session, card_id: str, player_id: int | None = None):
        result = await self.request(
            session.get, 'add_card',
            json={
                "player_id": player_id,
                "card_id": card_id,
            },
        )
        return result

    async def delete_player_card(self, session, card_id: str, player_id: int | None = None):
        result = await self.request(
            session.get, 'delete_player_card',
            json={
                "player_id": player_id,
                "card_id": card_id,
            },
        )
        return result

    async def create_game(self, session, admin_id: int):
        result = await self.request(
            session.get, 'create_game',
            json={
                "admin_id": admin_id,
            },
        )
        return result

    async def get_lobby_info(self, session, code: str):
        result = await self.request(
            session.get, 'get_lobby_info',
            json={
                "code": code,
            },
        )
        return result

    async def connect_to_game(self, session, code: str, player_id: int):
        result = await self.request(
            session.get, 'connect_to_game',
            json={
                "code": code,
                "player_id": player_id,
            },
        )
        return result

    async def leave_game(self, session, code: str, player_id: int):
        result = await self.request(
            session.get, 'leave_game',
            json={
                "code": code,
                "player_id": player_id,
            },
        )
        return result

    async def start_game(self, session, code: str):
        result = await self.request(
            session.get, 'start_game',
            json={
                "code": code,
            },
        )
        return result

    async def get_game_info(self, session, code: str):
        result = await self.request(
            session.get, 'get_game_info',
            json={
                "code": code,
            },
        )
        return result

    async def get_round_cards(self, session, code: str):
        result = await self.request(
            session.get, 'get_round_cards',
            json={
                "code": code,
            },
        )
        return result

    async def get_hand(self, session, code: str, player_id: int):
        result = await self.request(
            session.get, 'get_hand',
            json={
                "code": code,
                "player_id": player_id,
            },
        )
        return result

    async def send_riddle(self, session, code: str, player_id: int, riddle: str, card_id: str):
        result = await self.request(
            session.get, 'send_riddle',
            json={
                "code": code,
                "player_id": player_id,
                "riddle": riddle,
                "card_id": card_id,
            },
        )
        return result

    async def send_association(self, session, code: str, player_id: int, card_id: str):
        result = await self.request(
            session.get, 'send_association',
            json={
                "code": code,
                "player_id": player_id,
                "card_id": card_id,
            },
        )
        return result

    async def send_guess(self, session, code: str, player_id: int, card_id: str):
        result = await self.request(
            session.get, 'send_guess',
            json={
                "code": code,
                "player_id": player_id,
                "card_id": card_id,
            },
        )
        return result


async def send_association(code, player_id, card_id):
    """ For all non author players, adding imposter card """

    request = {
        "code": code,
        "player_id": player_id,
        "card_id": card_id,
    }
    return {
        "ok": True,
    }


async def send_guess(code, player_id, card_id):
    """ For all non author players, making guess after all player sent association """

    request = {
        "code": code,
        "player_id": player_id,
        "card_id": card_id,
    }
    return {
        "ok": True,
    }

api = API()
