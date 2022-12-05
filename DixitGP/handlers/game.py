import asyncio
import enum
import io
import logging

import aiogram
import aiohttp
from PIL import Image
from aiogram import Bot
from aiogram.utils.callback_data import CallbackData

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, ChatActions, InputMediaPhoto, InputFile
from aiogram.types import InlineKeyboardMarkup as Markup, InlineKeyboardButton as Button
from api import api
from utils import watermark

logger = logging.getLogger("handlers")
game_callbacks = CallbackData('game', 'type', 'args')


class GameState(enum.Enum):
    Lobby = enum.auto()
    AuthorRiddle = enum.auto()
    PlayersAssociations = enum.auto()
    PlayersGuesses = enum.auto()


class Game:
    def __init__(self, code):
        self.code = code
        self.state = GameState.Lobby
        self.players = set()

    def add_player(self, player):
        self.players.add(player)

    def remove_player(self, player):
        if player in self.players:
            self.players.remove(player)


class DixitState(StatesGroup):
    waiting_for_riddle = State()


class DixitEngine:
    def __init__(self):
        self.players = {}
        self.games = {}
        self.messages = {}

    def add(self, code, player, message):
        logger.info(f"DixitEngine.add {locals()}")
        if not (game := self.games.get(code)):
            game = Game(code)
            self.games[code] = game
        game.add_player(player)

        self.players[player] = code
        self.messages[player] = message

    def remove(self, code, player):
        logger.info(f"DixitEngine.remove {locals()}")
        if game := self.games.get(code):
            game.remove_player(player)
            if not game.players:
                self.games.pop(code)

        self.players.pop(player, None)
        self.messages.pop(player, None)

    def get_code(self, player):
        return self.players.get(player, None)

    def get_message_id(self, player):
        return self.messages.get(player, None)

    async def update_game_lobby(self, code):
        if not de.games.get(code):
            return
        async with aiohttp.ClientSession() as session:
            info = await api.get_lobby_info(session, code)

        text = f'Код гри {code}\n\n'
        mentions = await get_users_mention(*[p['player_id'] for p in info['players']])
        players = [f"{name}" + (" - ⭐️" if p['role'] == 'admin' else "")
                   for name, p in zip(mentions, info['players'])]
        text += "\n".join(players)

        from .start import start_callbacks
        for player_id, player in {i['player_id']: i for i in info['players']}.items():
            player_message = self.messages[player_id]
            markup = Markup(row_width=1)
            if player['role'] == 'admin':
                markup.add(
                    Button("Почати", callback_data=start_callbacks.new(type='start')),
                )
            markup.add(
                Button("Покинути гру", callback_data=start_callbacks.new(type='leave')),
            )
            self.messages[player_id] = await player_message.edit_text(text, reply_markup=markup)

    async def update_game_info(self, code):
        # bot = Bot.get_current()
        async with aiohttp.ClientSession() as session:
            info = (await api.get_game_info(session, code))['game_info']
        text = f"Очків для перемоги: {info['win_score']}\n\n"

        for player_id in self.games[code].players:
            await self.messages[player_id].edit_text(text, reply_markup=None)


async def send_players_hands(code):
    bot = Bot.get_current()
    async with aiohttp.ClientSession() as session:
        info = (await api.get_game_info(session, code))['game_info']
        author_id = info['author']['player_id']
        player_ids = [i['player_id'] for i in info['players']]

        hands_tasks = [
            api.get_hand(session, code, author_id),
            *[api.get_hand(session, code, i) for i in player_ids],
        ]
        author_hand, *players_hands = await asyncio.gather(*(asyncio.ensure_future(i) for i in hands_tasks))

    tasks = [bot.send_chat_action(i, ChatActions.UPLOAD_PHOTO) for i in [author_id, *player_ids]]
    await asyncio.gather(*(asyncio.ensure_future(i) for i in tasks))

    async def _send_media_hand(player_id, hand):
        files = []
        tasks = [bot.download_file_by_id(file) for file in hand]
        files_image = await asyncio.gather(*(asyncio.ensure_future(i) for i in tasks))

        for i, file in enumerate(files_image, start=1):
            image = Image.open(file)
            image = watermark.get_marked_image(image, i)
            x = io.BytesIO()
            image.save(x, format="jpeg")
            x.seek(0)
            files.append(InputMediaPhoto(InputFile(x)))
        await bot.send_media_group(player_id, files, protect_content=True)

    tasks = [
        _send_media_hand(author_id, author_hand['hand']),
        *[_send_media_hand(id_, h['hand']) for id_, h in zip(player_ids, players_hands)],
    ]
    await asyncio.gather(*(asyncio.ensure_future(i) for i in tasks))
    markup = Markup()
    count = len(author_hand['hand'])
    markup.add(*[Button(f"{i + 1}", callback_data=game_callbacks.new(type='riddle', args=f"{i}_{count}"))
                 for i in range(count)])
    await bot.send_message(author_id, "Оберіть одну з карток 👆", reply_markup=markup)


async def get_users_mention(*chat_ids):
    bot = Bot.get_current()
    tasks = [bot.get_chat(chat_id) for chat_id in chat_ids]
    result = await asyncio.gather(*(asyncio.ensure_future(i) for i in tasks))
    return [chat.mention for chat in result]


async def riddle_card(call: CallbackQuery, callback_data):
    user_id = call.message.chat.id
    code = de.get_code(user_id)
    card, count, *_ = callback_data.get("args").split('_')
    logger.info(f"riddle_card by user {user_id}, {code}")
    # async with aiohttp.ClientSession() as session:
    #     result = await api.leave_game(session, code, user_id)
    #
    # de.remove(code, user_id)
    # await de.update_game_lobby(code)
    # await call.message.edit_text("Ви залишили гру", reply_markup=None)
    await DixitState.waiting_for_riddle.set()
    await call.answer()


def register(dp: aiogram.Dispatcher):
    # dp.register_message_handler(start, commands=['start'], state="*")
    # dp.register_message_handler(connect_game_by_code, state=ConnectingState.waiting_for_game_code)
    dp.register_callback_query_handler(riddle_card, game_callbacks.filter(type='riddle'))
    # dp.register_callback_query_handler(connect_game, start_callbacks.filter(type='connect'))
    # dp.register_callback_query_handler(leave_game, start_callbacks.filter(type='leave'))
    # dp.register_callback_query_handler(start_game, start_callbacks.filter(type='start'))
    pass


de = DixitEngine()
