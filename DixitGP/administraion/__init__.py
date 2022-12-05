import asyncio
import logging
import shlex

import aiogram
from aiogram.utils.markdown import hpre

from logger import get_path as get_log_path

logger = logging.getLogger('bot.admin')
from config_reader import config
# from .config_reader import config
admins_ids = []
admins_ids.extend(
    [int(i) for i in config.ADMINS_IDS.replace(" ", '').replace(',', ' ').split()]
)


def register(dp: aiogram.Dispatcher):
    dp.register_message_handler(get_logs, commands=['get_logs'])
    dp.register_message_handler(execute, commands=['exec'])


async def get_logs(message: aiogram.types.Message):
    with open(get_log_path(), 'rt') as log_file:
        await message.reply_document(log_file)


async def execute(message: aiogram.types.Message):
    if message.from_user.id not in admins_ids:
        return
    args = shlex.split(message.text)[1:]
    if not args:
        return
    cmd = message.get_args()

    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)

    stdout, stderr = await proc.communicate()

    text = f'{cmd!r} exited with {proc.returncode}: '
    if stdout:
        text += f'[stdout]\n\n{hpre(stdout.decode())}'
    if stderr:
        text += f'[stderr]\n\n{hpre(stderr.decode())}'

    await message.reply(text)


async def on_startup(dp: aiogram.Dispatcher):
    for admin_id in admins_ids:
        await dp.bot.send_message(admin_id, "Started")
