import logging

import aiogram
import aiohttp
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup as Markup, InlineKeyboardButton as Button
from aiogram.types import Message, CallbackQuery
from aiogram.utils.callback_data import CallbackData

from api import api, APIError
from .game import de, send_players_hands

logger = logging.getLogger("handlers")
start_callbacks = CallbackData('start', 'type')


class ConnectingState(StatesGroup):
    waiting_for_game_code = State()


async def start(message: Message, state: FSMContext):
    await state.reset_state(with_data=False)
    user_id = message.chat.id
    if code := de.get_code(user_id):
        await message.answer(f"Ви вже в грі {code!r}")
        return
    text = "Вітаю, обери дію 😌"
    markup = Markup(row_width=1)
    markup.add(
        Button("Створити гру", callback_data=start_callbacks.new(type='create')),
        Button("Приеднатись до гри", callback_data=start_callbacks.new(type='connect')),
    )
    await message.answer(text, reply_markup=markup)
    # await send_players_hands("26F8F5")


async def create_game(call: CallbackQuery):
    admin_id = call.message.chat.id
    logger.info(f"create_game by user {admin_id}")
    async with aiohttp.ClientSession() as session:
        try:
            result = await api.create_game(session, admin_id)
            code = result['code']
        except APIError as e:
            logger.error("Unexpected error: {!r}".format(e))
            return
    await call.message.edit_text(call.message.text, reply_markup=None)

    m = await call.message.answer("Завантаження.. ⏳")
    de.add(code, admin_id, m)
    await de.update_game_lobby(code)
    await call.answer()


async def connect_game(call: CallbackQuery):
    user_id = call.message.chat.id
    logger.info(f"connect_game by user {user_id}")
    await ConnectingState.waiting_for_game_code.set()
    await call.message.edit_text("Надішліть код гри", reply_markup=None)
    await call.answer()


async def connect_game_by_code(message: Message, state: FSMContext):
    user_id = message.chat.id
    code = str(message.text).upper()
    logger.info(f"connect_game_by_code by user {user_id}, {code}")
    async with aiohttp.ClientSession() as session:
        try:
            result = await api.connect_to_game(session, code, user_id)
        except APIError as e:
            result = e.args[0]
            if "no game" in result['error_message'].lower():
                await message.reply("Гру не знайдено")
                return
            if "player already exists" in result['error_message'].lower():
                await message.answer("Ви вже у грі")
                # todo: send some lobby info
                return
            logger.error("Unexpected error: {!r}".format(e))
            return

    m = await message.answer("Завантаження.. ⏳")
    de.add(code, user_id, m)
    await de.update_game_lobby(code)

    await state.reset_state(with_data=False)


async def leave_game(call: CallbackQuery):
    user_id = call.message.chat.id
    code = de.get_code(user_id)
    logger.info(f"leave_game by user {user_id}, {code}")
    async with aiohttp.ClientSession() as session:
        result = await api.leave_game(session, code, user_id)

    de.remove(code, user_id)
    await de.update_game_lobby(code)
    await call.message.edit_text("Ви залишили гру", reply_markup=None)
    await call.answer()


async def start_game(call: CallbackQuery):
    user_id = call.message.chat.id
    code = de.get_code(user_id)
    logger.info(f"start_game by user {user_id}, {code}")
    async with aiohttp.ClientSession() as session:
        result = await api.start_game(session, code)

    await call.answer()
    await de.update_game_info(code)
    await send_players_hands(code)


def register(dp: aiogram.Dispatcher):
    dp.register_message_handler(start, commands=['start'], state="*")
    dp.register_message_handler(connect_game_by_code, state=ConnectingState.waiting_for_game_code)
    dp.register_callback_query_handler(create_game, start_callbacks.filter(type='create'))
    dp.register_callback_query_handler(connect_game, start_callbacks.filter(type='connect'))
    dp.register_callback_query_handler(leave_game, start_callbacks.filter(type='leave'))
    dp.register_callback_query_handler(start_game, start_callbacks.filter(type='start'))
