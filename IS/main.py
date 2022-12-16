import asyncio
import time

import aiogram
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config_reader import config
from logger import init_logging

RECONNECT_TIME = 60


async def error_handler(update: aiogram.types.Update, exception):
    message = update.message
    if update.callback_query:
        await update.callback_query.answer("🤨", show_alert=True)
        message = update.callback_query.message

    logger.exception(f"error_handler: {exception!r}. {update}")
    await update.bot.send_message(738016227, f'{message.chat} fails:\n{exception!r}')
    await message.reply("🤨")
    return True


async def set_commands(bot: aiogram.Bot):
    commands = [
        BotCommand(command="/start", description="Почати вібор гри"),
        BotCommand(command="/cards", description="Переглянути існуючі картки"),
    ]
    await bot.set_my_commands(commands)


def create_dispatcher():
    import handlers
    import administraion
    bot = aiogram.Bot(config.BOT_TOKEN.get_secret_value(), parse_mode='HTML')
    dp = aiogram.Dispatcher(bot, storage=MemoryStorage())
    from middlwares import MiddlewareUserAuthorized
    dp.middleware.setup(MiddlewareUserAuthorized())
    handlers.register(dp)
    administraion.register(dp)

    dp.register_errors_handler(error_handler, exception=BaseException)
    return dp


async def _main():
    dp = create_dispatcher()
    logger.info(f"Starting bot... {await dp.bot.get_me()}")
    await set_commands(dp.bot)
    import administraion
    await administraion.on_startup(dp)
    try:
        await dp.start_polling()
    except BaseException as error:
        raise error
    finally:
        del dp


def main():
    # aiogramwrap.wrap_all()
    while True:
        try:
            asyncio.run(_main())
            break

        except aiogram.exceptions.NetworkError as e:
            logger.error(f'Error! Try reconnect in {RECONNECT_TIME} secs. {e!r}')
            time.sleep(RECONNECT_TIME)


logger = init_logging()

try:
    main()
except KeyboardInterrupt:
    pass
except BaseException as e:
    logger.exception(f'main except: {e!r}')
