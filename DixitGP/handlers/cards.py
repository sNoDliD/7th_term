import asyncio
import io
import os.path
import time
from collections import defaultdict
from pathlib import Path

import aiogram
import aiohttp
from PIL import Image
from aiogram.types import ContentType, Message, PhotoSize, MediaGroup, InputMedia, InputMediaPhoto, InputFile, \
    ChatActions

from api import api
from utils import watermark


def register(dp: aiogram.Dispatcher):
    dp.register_message_handler(view_count, commands=['cards'], state='*')
    dp.register_message_handler(general, content_types=ContentType.ANY, state='*')


async def view_count(message: Message):
    async with aiohttp.ClientSession() as session:
        total = await api.get_player_cards(session, None)
        player_card = await api.get_player_cards(session, message.chat.id)
        # for i in player_card['cards']:
        #     await api.delete_player_card(session, i, message.chat.id)
    await message.reply(f"Загальні - {len(total['cards'])}\nДодаткові - {len(player_card['cards'])}")


async def general(message: Message):
    if message.photo:
        photo: PhotoSize = message['photo'][-1]

        # path = Path("photos") / f"{photo.file_unique_id}.jpeg"
        # start_time = time.time()
        # if not os.path.exists(path):
        #     await photo.download(destination_file=f"photos/{photo.file_unique_id}.jpeg")
        async with aiohttp.ClientSession() as session:
            result = await api.add_card(session, photo.file_id, message.chat.id)
        print(photo.file_unique_id, photo.file_id, result, sep=', ')
        # if message.media_group_id:
        #     general.groups[message.media_group_id].append(path)
        #     await ChatActions.upload_photo(1.5)
        #     paths = general.groups.pop(message.media_group_id, None)
        #     if not paths:
        #         return
        #     files = []
        #     for i, path in enumerate(paths, start=1):
        #         image = Image.open(path)
        #         image = watermark.get_marked_image(image, i)
        #         x = io.BytesIO()
        #         image.save(x, format="jpeg")
        #         x.seek(0)
        #         files.append(InputMediaPhoto(InputFile(x)))
        #     await message.answer_media_group(files)
        # else:
        #     image = Image.open(path)
        #     image = watermark.get_marked_image(image, int(time.time() % 11))
        #     x = io.BytesIO()
        #     image.save(x, format="jpeg")
        #     x.seek(0)
        #
        #     await message.answer_photo(InputFile(x))

general.groups = defaultdict(list)
