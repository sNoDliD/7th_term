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
            try:
                data = await resp.json()
            except aiohttp.ContentTypeError:
                data = await resp.text()
            if isinstance(data, dict) and not data.get("ok", True):
                raise APIError(data)
        return data

    async def get_user(self, session, user_id: int):
        return await self.request(session.get, f'user/{user_id}')

    async def add_user(self, session, user_id: int, name: str, number: str):
        result = await self.request(
            session.post, f'user',
            json={
                "userId": user_id,
                "userName": name,
                "phoneNumber": number,
            }
        )
        return result

    async def get_locations(self, session):
        return await self.request(session.get, f'space')

    async def get_barbers(self, session, date):
        return await self.request(session.get, f'barber', params={"date": date})

    async def get_barber_free_time(self, session, barber, date):
        return await self.request(session.get, f'barber/{barber}', params={"date": date})

    async def do_book(self, session, user_id, barber, date, time):
        return await self.request(session.post, f'book', json={
            "userId": user_id,
            "barberName": barber,
            "date": date,
            "time": time,
        })


api = API()
