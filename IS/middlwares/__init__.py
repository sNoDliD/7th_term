import aiohttp
from aiogram import Dispatcher
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware
from aiogram.types import Message, CallbackQuery, KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from api import api, APIError
from handlers.book import start_booking


class MiddlewareUserAuthorized(LifetimeControllerMiddleware):
    async def pre_process(self, obj, data, *args):
        if isinstance(obj, Message):
            call, message = None, obj
        elif isinstance(obj, CallbackQuery):
            call, message = obj, obj.message
        else:
            return

        user_id = message.chat.id
        if user_id < 0:
            raise CancelHandler

        async with aiohttp.ClientSession() as session:
            try:
                user_info = await api.get_user(session, user_id)
            except APIError:
                user_info = None
        if user_info:
            return
        state = Dispatcher.get_current().current_state()
        async with state.proxy() as data:
            contact = data.get('contact')

        if contact and message.text:
            async with aiohttp.ClientSession() as session:
                await api.add_user(session, user_id, message.text, contact.phone_number)
            await start_booking()
            raise CancelHandler

        if (contact and not message.text) or (contact := message.contact):
            async with state.proxy() as data:
                data['contact'] = contact
            text = "Надішліть ваше ім'я по якому можно до вас звертатись"
            m = await message.answer(text, reply_markup=ReplyKeyboardRemove())
            # await # todo: skip button with profile name
            raise CancelHandler

        text = "Привіт, спочатку необхідно зарєестуватись в системі 😇\n\nБудь ласка надішліть свій номер телефону 📞"
        markup = ReplyKeyboardMarkup(one_time_keyboard=True)
        markup.add(KeyboardButton("✉️ Надіслати", request_contact=True))
        await message.answer(text, reply_markup=markup)
        raise CancelHandler

    # async def post_process(self, obj, data, *args):
    #     chat = types.Chat.get_current()
    #     if chat:
    #         User.clear_cache(chat.id)
    #
    #     if isinstance(obj, CallbackQuery):
    #         async with Dispatcher.get_current().current_state().proxy() as data:
    #             if not data.get('markup_saved', None):
    #                 await set_last_message(obj.message)
    #
    #         await obj.answer()
