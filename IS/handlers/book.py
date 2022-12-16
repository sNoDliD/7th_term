import datetime
import logging

import aiogram
import aiohttp
from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup as Markup, InlineKeyboardButton as Button
from aiogram.types import Message, CallbackQuery
from aiogram.utils.callback_data import CallbackData

from api import api, APIError
from utils import number_to_emojis

# from .game import de, send_players_hands

logger = logging.getLogger("handlers")
book_callbacks = CallbackData('book', 'type', 'args')


class BookingState(StatesGroup):
    waiting_for_location = State()
    waiting_for_query_type = State()
    waiting_for_barber = State()
    waiting_for_time = State()


def get_message():
    message = Message.get_current()
    if not message:
        message = CallbackQuery.get_current().message
    return message


async def any_message(message: Message):
    await start_booking()


async def start_booking(edit_query_message=False):
    state = Dispatcher.get_current().current_state()
    await state.reset_data()
    message = get_message()
    async with aiohttp.ClientSession() as session:
        locations = await api.get_locations(session)
    locations_names = [i['address'] for i in locations]
    markup = Markup(row_width=1)
    markup.add(
        *[Button(name, callback_data=book_callbacks.new(type='address', args=str(i)))
          for i, name in enumerate(locations_names)]
    )
    if edit_query_message:
        method = CallbackQuery.get_current().message.edit_text
    else:
        method = message.answer
    await method("Оберіть, будь ласка, зручну локацію", reply_markup=markup)
    # await BookingState.waiting_for_location.set()


async def address_selected(call: CallbackQuery):
    user_id = call.message.chat.id
    logger.info(f"address_selected by user {user_id}")
    rows = call.message.reply_markup.inline_keyboard
    clicked = next(filter(lambda x: x.callback_data == call.data,
                          [b for r in rows for b in r]))

    location = clicked.text
    state = Dispatcher.get_current().current_state()
    async with state.proxy() as data:
        data['location'] = location

    await start_date_selection()
    await call.answer()
    # await BookingState.waiting_for_query_type.set()


async def start_date_selection():
    message = get_message()
    state = Dispatcher.get_current().current_state()
    async with state.proxy() as data:
        location = data['location']
    text = f'Коли вам буде зручно прийти до нас у локацію <code>{location}</code>?'
    # markup = Markup(row_width=1)
    # # todo: change button to "Змінити час або барбера"
    # markup.add(
    #     Button("Обрати барбера 💇", callback_data=book_callbacks.new(type='type', args='barber')),
    #     Button("Обрати час 🕓", callback_data=book_callbacks.new(type='type', args='time')),
    # )
    # # todo: add button "confirm" if selected data OK
    markup = Markup(row_width=4)
    now = datetime.datetime.now()
    days = [now + datetime.timedelta(days=i) for i in range(8)]
    markup.add(*[Button(d.strftime('%d.%m'),
                        callback_data=book_callbacks.new(type='date', args=d.strftime('%Y-%m-%d')))
                 for d in days])
    markup.row(Button("Повернутись ❎", callback_data=book_callbacks.new(type='back', args='locations')))
    await message.edit_text(text, reply_markup=markup)


async def date_selected(call: CallbackQuery, callback_data):
    user_id = call.message.chat.id
    date = callback_data.get("args")
    logger.info(f"date_selected by user {user_id}: {date}")

    state = Dispatcher.get_current().current_state()
    async with state.proxy() as data:
        data['date'] = date
    await start_barber_selection()
    await call.answer()


async def start_barber_selection(page=0):
    state = Dispatcher.get_current().current_state()
    async with state.proxy() as data:
        data['barber_page'] = page
        date = data['date']

    async with aiohttp.ClientSession() as session:
        barbers = await api.get_barbers(session, date)
        logger.info(f"Barbers on {date}: {barbers}")

    markup = Markup(row_width=1)
    barbers_per_page = 2
    if barbers:
        page_barbers = barbers[page * barbers_per_page: (page + 1) * barbers_per_page]
        # markup.row(Button("👉 Будь-який 👈", callback_data=book_callbacks.new(type='barber', args='')))  # todo
        markup.add(*[Button(f"{b['name']}, {b['rating']}🌟 {b['cost']}₴",
                            callback_data=book_callbacks.new(type='barber', args=b['name']))
                     for b in page_barbers])

        buttons = []
        if page > 0:
            buttons.append(Button("⬅️", callback_data=book_callbacks.new(type='back', args=f'barber_{page - 1}')))
        if len(barbers) > barbers_per_page:
            buttons.append(Button(number_to_emojis(page + 1), callback_data=book_callbacks.new(type='back', args='null')))
        if len(barbers) > barbers_per_page * (page + 1):
            buttons.append(Button("➡️", callback_data=book_callbacks.new(type='back', args=f'barber_{page + 1}')))
        markup.row(*buttons)
        text = "Обрати барбера 💇"
    else:
        text = "Нажаль немає вільних барберів в цей день 🤷‍♂️"

    markup.row(Button("Повернутись ❎", callback_data=book_callbacks.new(type='back', args='date')))
    await get_message().edit_text(text, reply_markup=markup)


async def barber_selected(call: CallbackQuery, callback_data):
    user_id = call.message.chat.id
    barber = callback_data.get("args")
    logger.info(f"barber_selected by user {user_id}: {barber}")

    state = Dispatcher.get_current().current_state()
    async with state.proxy() as data:
        data['barber'] = barber
    await call.answer()
    await start_choice_time()


async def start_choice_time():
    state = Dispatcher.get_current().current_state()
    async with state.proxy() as data:
        barber_page = data['barber_page']
        barber = data['barber']
        date = data['date']

    async with aiohttp.ClientSession() as session:
        free_time = await api.get_barber_free_time(session, barber, date)
        logger.info(f"Barber {barber} at {date} free_time: {free_time}")

    working_time = [i for i in free_time if 9 <= i <= 20]
    markup = Markup(row_width=3)
    markup.add(
        *[Button(f"{i:0>2}:00-{i+1:0>2}:00", callback_data=book_callbacks.new(type='time', args=f"{i}")) for i in working_time]
    )
    markup.row(Button("Повернутись ❎", callback_data=book_callbacks.new(type='back', args=f"barber_{barber_page}")))
    text = "Оберіть зручний час 🕓"
    await get_message().edit_text(text, reply_markup=markup)


async def time_selected(call: CallbackQuery, callback_data):
    user_id = call.message.chat.id
    time = callback_data.get("args")
    logger.info(f"time_selected by user {user_id}: {time}")

    state = Dispatcher.get_current().current_state()
    async with state.proxy() as data:
        data['time'] = int(time)
    await request_confirmation()


async def request_confirmation():
    state = Dispatcher.get_current().current_state()
    async with state.proxy() as data:
        location = data['location']
        date = data['date']
        barber = data['barber']
        time = data['time']
    formatted_time = f"{time:0>2}:00-{time + 1:0>2}:00"
    text = f"Підвердіть чи все правильно:\n" \
           f"🏠 - {location}\n" \
           f"📆 - {date.replace('-', '.')} {formatted_time}\n" \
           f"💇 - {barber}"
    markup = Markup(row_width=1)
    markup.add(
        Button("Підтвердити ✅", callback_data=book_callbacks.new(type="confirm", args="")),
    )
    markup.row(Button("Повернутись ❎", callback_data=book_callbacks.new(type='back', args=f"time")))
    await get_message().edit_text(text, reply_markup=markup)


async def confirm(call: CallbackQuery):
    user_id = call.message.chat.id
    logger.info(f"confirm by user {user_id}")
    state = Dispatcher.get_current().current_state()
    async with state.proxy() as data:
        location = data['location']
        date = data['date']
        barber = data['barber']
        time = data['time']

    message = get_message()
    await message.edit_text(message.text, reply_markup=None)
    async with aiohttp.ClientSession() as session:
        try:
            await api.do_book(session, user_id, barber, date, time)
        except APIError:
            await message.answer("Шось пілно не так, спробуйне ще раз 😔")
            await start_booking()
            return
    await message.answer("Вітаемо вас записано на прийом! 😊")
    await state.reset_state(with_data=True)


async def back(call: CallbackQuery, callback_data):
    user_id = call.message.chat.id
    logger.info(f"back by user {user_id}, {callback_data}")
    match callback_data['args'].split("_"):
        case ["locations"]:
            await start_booking(edit_query_message=True)
        case ["date"]:
            await start_date_selection()
        case ["barber", page]:
            await start_barber_selection(int(page))
        case ["time"]:
            await start_choice_time()
    await call.answer()


def register(dp: aiogram.Dispatcher):
    dp.register_message_handler(any_message)
    dp.register_callback_query_handler(address_selected, book_callbacks.filter(type='address'))
    # dp.register_callback_query_handler(query_by_barber, book_callbacks.filter(type='type', args='barber'),
    #                                    state=BookingState.waiting_for_query_type)
    # dp.register_callback_query_handler(query_by_time, book_callbacks.filter(type='type', args='time'),
    #                                    state=BookingState.waiting_for_query_type)
    dp.register_callback_query_handler(back, book_callbacks.filter(type='back'), state="*")
    dp.register_callback_query_handler(date_selected, book_callbacks.filter(type='date'))
    dp.register_callback_query_handler(barber_selected, book_callbacks.filter(type='barber'))
    dp.register_callback_query_handler(time_selected, book_callbacks.filter(type='time'))
    dp.register_callback_query_handler(confirm, book_callbacks.filter(type='confirm'))
