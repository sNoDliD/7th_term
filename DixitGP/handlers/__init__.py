import typing

if typing.TYPE_CHECKING:
    import aiogram

from . import cards
from . import start
from . import game


def register(dp: "aiogram.Dispatcher"):
    start.register(dp)
    cards.register(dp)
    game.register(dp)
