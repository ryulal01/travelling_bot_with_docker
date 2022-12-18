import time

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from app.models import User, CityCountry, UserVisited
from app.utils import location_await_query_country_city
from config.db import session


class FindCommentsByCityState(StatesGroup):
	waiting_for_city = State()


async def find_comments_by_city_start(message: types.Message, state: FSMContext):
	user_in_db = session.query(User).filter(
		User.user_id_tg == message.from_user.id).first()
	if not user_in_db:
		await message.answer(
			f"Вы еще не зарегистрировались ")
		await message.answer(
			f"""нажмите /registration для прохождения регистрации"""
		)
		return

	await message.answer(f"Здесь вы получите до 3 комментариев по городу")
	await message.answer(f"скопируйте и вставьте название бота ниже")
	await message.answer(f"@{(await message.bot.get_me()).username}")
	await message.answer("далее вводите город на русском языке")
	await state.set_state(FindCommentsByCityState.waiting_for_city.state)


async def city_given(message: types.Message, state: FSMContext):
	via_bot = message.via_bot
	if via_bot is None or via_bot.id != message.bot.id:
		await message.answer('Требуется прислать именно через этого бота')
		await message.answer(f"скопируйте и вставьте название бота ниже")
		await message.answer(f"@{(await message.bot.get_me()).username}")
		await message.answer("далее вводите город на русском языке")
		return
	if not '|' in message.text or not ':' in message.text:
		await message.answer('Что-то не то, попробуйте, еще раз!')
		return
	country, city = message.text.lower().split(' | ')

	country_clean = country.split(':')[-1].strip().capitalize()
	city_clean = city.split(':')[-1].strip().capitalize()

	country_obj = session.query(CityCountry).filter(
		CityCountry.city_name == city_clean,
		CityCountry.country_name == country_clean).first()
	if not country_obj:
		await message.answer(
			f"Пока никто не комментировал этот город")
		await state.finish()
		return

	existed_objs = session.query(UserVisited).filter(
		UserVisited.country_rel == country_obj.id).order_by(
		UserVisited.created_on.desc()).limit(3).all()

	await message.answer(
		f"Найдено комментариев: {len(existed_objs)}\n"
		f"Покажем до 3 комментариев, сначала самые свежие"
	)
	for obj in existed_objs:
		await message.answer(
			f"Пользователь: {obj.user.name}\n"
			f"Страна: {obj.country.country_name}\n"
			f"Город: {obj.country.city_name}\n"
			f"Месяц: {obj.month.name}\n"
			f"Оценка: {obj.voted}\n"
			f"Сам комментарий: {obj.comment_visited}\n"
		)
		time.sleep(1)


def register_handlers_find_comments_by_city(dp: Dispatcher):
	dp.register_message_handler(find_comments_by_city_start,
								commands = "find_comments_by_city",
								state = "*")
	dp.register_inline_handler(location_await_query_country_city,
								state = FindCommentsByCityState.waiting_for_city)
	dp.register_message_handler(city_given,
								state = FindCommentsByCityState.waiting_for_city)
