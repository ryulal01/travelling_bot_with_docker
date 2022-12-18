import asyncio
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from app.handlers.create_comment_visited_places import \
	register_handlers_create_comment_visited_place
from app.handlers.common import register_handlers_common
from app.handlers.get_comments_by_city import \
	register_handlers_find_comments_by_city
from app.handlers.last_comments import register_handlers_find_last_comments
from app.handlers.low_price_ticket_find import \
	register_handlers_find_low_price_avia_tickets
from app.handlers.registration import register_handlers_registration

from config.tokens import TOKEN_TG


async def set_commands(bot: Bot):
	commands = [
		BotCommand(command = "/registration",
				   description = "Зарегистрироваться"),
		BotCommand(command = "/create_comment_city",
				   description = "Прокомментировать город"),
		BotCommand(command = "/find_comments_by_city",
				   description = "Посмотреть комментарии о городе"),
		BotCommand(command = "/find_last_comments",
				   description = "Посмотреть последние комментарии в системе"),
		BotCommand(command = "/find_low_price_avia_tickets",
				   description = "Найти дешевый авиабилет"),
		BotCommand(command = "/cancel",
				   description = "Отменить текущее действие"),
	]
	await bot.set_my_commands(commands)


async def main():

	bot = Bot(token = TOKEN_TG)
	dp = Dispatcher(bot, storage = MemoryStorage())

	register_handlers_common(dp)
	register_handlers_registration(dp)
	register_handlers_create_comment_visited_place(dp)
	register_handlers_find_low_price_avia_tickets(dp)
	register_handlers_find_comments_by_city(dp)
	register_handlers_find_last_comments(dp)

	await set_commands(bot)

	await dp.start_polling()


if __name__ == '__main__':
	asyncio.run(main())
