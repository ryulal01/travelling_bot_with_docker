import time
from aiogram import Dispatcher, types

from app.models import UserVisited

from config.db import session


async def find_last_comments_start(message: types.Message):
	existed_objs = session.query(UserVisited).order_by(
		UserVisited.created_on.desc()).limit(3).all()

	if not existed_objs:
		await message.answer(
			f"Пока в системе нет комментариев о городах\n"
		)
		return

	await message.answer(
		f"Найдено комментариев: {len(existed_objs)}\n"
		f"Покажем до 3 комментариев, сначала самые свежие"
	)
	for obj in existed_objs:
		await message.answer(
			f"Страна: {obj.country.country_name}\n"
			f"Город: {obj.country.city_name}\n"
			f"Месяц: {obj.month.name}\n"
			f"Оценка: {obj.voted}\n"
			f"Сам комментарий: {obj.comment_visited}\n"
		)
		time.sleep(1)


def register_handlers_find_last_comments(dp: Dispatcher):
	dp.register_message_handler(find_last_comments_start,
								commands = "find_last_comments",
								state = "*")
