from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from app.models import User, UserVisited, CityCountry, Month
from app.utils import get_or_create, location_await_query_country_city
from config.db import session

from app.utils import DICT_MONTHS


class CreateCommentPlaceState(StatesGroup):
	waiting_for_register_location = State()
	waiting_for_date_month_visited = State()
	waiting_for_voted = State()
	waiting_for_comment_visited = State()


async def create_comment_start(message: types.Message, state: FSMContext):
	user_in_db = session.query(User).filter(
		User.user_id_tg == message.from_user.id).first()
	if not user_in_db:
		await message.answer(
			f"Вы еще не зарегистрировались"
			f"нажмите /registration для прохождения регистрации")
		return

	await message.answer(f"скопируйте и вставьте название бота ниже")
	await message.answer(f"@{(await message.bot.get_me()).username}")
	await message.answer("далее вводите город на русском языке")
	await state.update_data(user_id = message.from_user.id)
	await state.set_state(
		CreateCommentPlaceState.waiting_for_register_location.state)


async def register_location(message: types.Message, state: FSMContext):
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

	previous_comment_data = await state.get_data()
	country_obj = get_or_create(
		session,
		CityCountry,
		city_name = city_clean,
		country_name = country_clean)
	user_obj = session.query(User).filter(
		User.user_id_tg == previous_comment_data.get('user_id')).first()

	if not all([user_obj, country_obj]):
		await message.answer(
			f"Произошла непредвиденная ошибка, попробуйте позже")
		await state.finish()
		return

	existed_obj = session.query(UserVisited).filter(
		UserVisited.user_rel == user_obj.id,
		UserVisited.country_rel == country_obj.id).first()

	if existed_obj:
		await message.answer(
			f"Уже есть запись сделанная вами про этот город")
		await message.answer(
			f"Страна: {existed_obj.country.country_name}\n"
			f"Город: {existed_obj.country.city_name}\n"
			f"Месяц: {existed_obj.month.name}\n"
			f"Оценка: {existed_obj.voted}\n"
			f"Сам комментарий: {existed_obj.comment_visited}\n"
		)
		await message.answer(f"Попробуйте другой город")
		await message.answer(f"скопируйте и вставьте название бота ниже")
		await message.answer(f"@{(await message.bot.get_me()).username}")
		await message.answer("далее вводите город на русском языке")
		return

	months_obj = session.query(Month).all()
	if not months_obj:
		try:
			obj_to_commit = [Month(id = month.get('id'), name = month.get('name'),
								   name_id = month.get('name_id')) for month in
							 DICT_MONTHS]
			session.bulk_save_objects(obj_to_commit)
			session.commit()
		except Exception:
			session.rollback()
			await message.answer(
				'Месяцы ушли к костру по мотивам сказки С.Я. Маршака!')
			await state.finish()
			return
		else:
			months_obj = session.query(Month).all()
	buttons = [
		types.InlineKeyboardButton(text = row.name,
								   callback_data = f'mcomment|||{row.name_id}',
								   ) for row in months_obj]

	keyboard = types.InlineKeyboardMarkup(row_width = 3)
	keyboard.add(*buttons)
	await state.update_data(given_country = country_clean)
	await state.update_data(given_city = city_clean)

	await message.answer(f"Теперь выберите месяц",
						 reply_markup = keyboard)

	await state.set_state(
		CreateCommentPlaceState.waiting_for_date_month_visited.state)


async def date_given_month(call: types.CallbackQuery, state: FSMContext):
	month_num = int(call.data.split("|||")[-1])
	await call.message.delete_reply_markup()  # удаляем клавиатуру
	buttons = [
		types.InlineKeyboardButton(text = vote,
								   callback_data = f'comment_vote|||{vote}',
								   ) for vote in range(1, 6)]

	keyboard = types.InlineKeyboardMarkup(row_width = 3)
	keyboard.add(*buttons)
	await state.update_data(given_date_m = month_num)
	await call.message.answer(f"Теперь поставьте оценку вашей поездке",
							  reply_markup = keyboard)
	await state.set_state(CreateCommentPlaceState.waiting_for_voted.state)


async def vote_given(call: types.CallbackQuery, state: FSMContext):
	vote_num = int(call.data.split("|||")[-1])
	await call.message.delete_reply_markup()  # удаляем клавиатуру
	await state.update_data(given_vote = vote_num)
	await call.message.answer(f"Теперь напишите комментарий к вашей поездке")
	await state.set_state(
		CreateCommentPlaceState.waiting_for_comment_visited.state)


async def comment_visited_given(message: types.Message, state: FSMContext):
	comment = message.text
	previous_comment_data = await state.get_data()
	country_name = previous_comment_data.get('given_country')
	city_name = previous_comment_data.get('given_city')

	country_obj = get_or_create(session, CityCountry, city_name = city_name,
								country_name = country_name)

	user_obj = session.query(User).filter(
		User.user_id_tg == previous_comment_data.get('user_id')).first()

	month_obj = session.query(Month).filter(
		Month.name_id == previous_comment_data.get('given_date_m')).first()

	if not all([month_obj, user_obj, country_obj]):
		await message.answer(
			f"Произошла непредвиденная ошибка, попробуйте позже")
		await state.finish()
		return
	comment_obj = UserVisited(
		voted = previous_comment_data.get('given_vote'),
		comment_visited = comment,
		user_rel = user_obj.id,
		country_rel = country_obj.id,
		month_rel = month_obj.id,
	)

	try:
		session.add(comment_obj)
		session.commit()
	except Exception as e:
		print(e)
		session.rollback()
		await message.answer(
			f"Какой то сбой, попробуйте позже\n")
		await state.finish()
	else:
		await message.answer(
			f"Сохранили комментарий!\n"
			f"Страна: {comment_obj.country.country_name}\n"
			f"Город: {comment_obj.country.city_name}\n"
			f"Месяц: {comment_obj.month.name}\n"
			f"Оценка: {comment_obj.voted}\n"
			f"Сам комментарий: {comment_obj.comment_visited}\n"
		)
		await state.finish()


def register_handlers_create_comment_visited_place(dp: Dispatcher):
	dp.register_message_handler(create_comment_start,
								commands = 'create_comment_city',
								state = "*")
	dp.register_inline_handler(location_await_query_country_city,
							   state = CreateCommentPlaceState.waiting_for_register_location)
	dp.register_message_handler(register_location,
								state = CreateCommentPlaceState.waiting_for_register_location)
	dp.register_callback_query_handler(date_given_month,
									   state = CreateCommentPlaceState.waiting_for_date_month_visited)
	dp.register_callback_query_handler(vote_given,
									   state = CreateCommentPlaceState.waiting_for_voted)
	dp.register_message_handler(comment_visited_given,
								state = CreateCommentPlaceState.waiting_for_comment_visited)
