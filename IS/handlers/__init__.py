import typing

if typing.TYPE_CHECKING:
    import aiogram

from . import book


def register(dp: "aiogram.Dispatcher"):
    book.register(dp)
