from datetime import datetime

import requests
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from app.models import Month
from app.utils import HEADERS, location_await_query_code_country_city
from config.db import session
from config.tokens import TOKEN_AVIASALES

from app.utils import DICT_MONTHS


class LowPriceTicketState(StatesGroup):
	waiting_for_register_location_from = State()
	waiting_for_register_location_to = State()
	waiting_for_date_month_visited = State()


async def tickets_start(message: types.Message, state: FSMContext):
	await message.answer(f"Из какого города планируете лететь?")
	await message.answer(f"скопируйте и вставьте название бота ниже")
	await message.answer(f"@{(await message.bot.get_me()).username}")
	await message.answer("далее вводите город на русском языке")
	await state.update_data(user_id = message.from_user.id)
	await state.set_state(
		LowPriceTicketState.waiting_for_register_location_from.state)


async def register_location_from(message: types.Message, state: FSMContext):
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

	country_city, code_airport = message.text.split(' | ')
	code_airport = code_airport.split(':')[-1].strip().capitalize()

	await state.update_data(country_city_from = country_city.strip())
	await state.update_data(code_airport_from = code_airport.strip())

	await message.answer(f"В какой город планируете лететь?")
	await message.answer(f"скопируйте и вставьте название бота ниже")
	await message.answer(f"@{(await message.bot.get_me()).username}")
	await message.answer("далее вводите город на русском языке")

	await state.set_state(
		LowPriceTicketState.waiting_for_register_location_to.state)


async def register_location_to(message: types.Message, state: FSMContext):
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

	country_city, code_airport = message.text.split(' | ')
	code_airport = code_airport.split(':')[-1].strip().capitalize()

	await state.update_data(country_city_to = country_city.strip())
	await state.update_data(code_airport_to = code_airport.strip())

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

	await message.answer(f"Теперь выберите месяц",
						 reply_markup = keyboard)

	await state.set_state(
		LowPriceTicketState.waiting_for_date_month_visited.state)


async def date_given_month(call: types.CallbackQuery, state: FSMContext):
	month_num = int(call.data.split("|||")[-1])
	await call.message.delete_reply_markup()

	current_month = datetime.now().month
	current_year = datetime.now().year
	if month_num < current_month:
		current_year += 1

	if month_num < 10:
		month_num = f"0{month_num}"

	previous_data_got = await state.get_data()
	code_airport_from = previous_data_got.get('code_airport_from')
	code_airport_to = previous_data_got.get('code_airport_to')

	url = f'https://api.travelpayouts.com/v1/prices/calendar?departure_date={current_year}-{month_num}&origin={code_airport_from}&destination={code_airport_to}&calendar_type=departure_date&token={TOKEN_AVIASALES}'
	r = requests.get(url = url, headers = HEADERS)
	response_json = r.json()
	if not response_json.get('success'):
		await call.message.answer(
			'Пока нет результатов по вашему направлению, попробуйте позже')
		await state.finish()
		return
	resp_data = response_json.get('data')

	cheaper = None
	for date in resp_data:
		if not cheaper:
			cheaper = resp_data.get(date)
			continue
		if cheaper.get('price') > resp_data.get(date).get('price'):
			cheaper = resp_data.get(date)
	departure_date_at = cheaper.get('departure_at').split('T')[0]
	return_date_at = cheaper.get('return_at').split('T')[0]
	await call.message.answer(
		f"Самый дешевый билет на даты:\n"
		f"Туда: {departure_date_at} | Обратно: {return_date_at}\n"
		f"Из: {previous_data_got.get('country_city_from')} | В: {previous_data_got.get('country_city_to')}\n"
		f"Цена: {cheaper.get('price')}\n"
		f"Пересадок: {cheaper.get('transfers')}\n"
		f"Авиакомпания: {cheaper.get('airline')}\n"
		f"Рейс: {cheaper.get('flight_number')}"
	)
	await state.finish()


def register_handlers_find_low_price_avia_tickets(dp: Dispatcher):
	dp.register_message_handler(tickets_start,
								commands = 'find_low_price_avia_tickets',
								state = "*")

	dp.register_inline_handler(location_await_query_code_country_city,
							   state = LowPriceTicketState.waiting_for_register_location_from)
	dp.register_message_handler(register_location_from,
								state = LowPriceTicketState.waiting_for_register_location_from)
	dp.register_inline_handler(location_await_query_code_country_city,
							   state = LowPriceTicketState.waiting_for_register_location_to)
	dp.register_message_handler(register_location_to,
								state = LowPriceTicketState.waiting_for_register_location_to)
	dp.register_callback_query_handler(date_given_month,
									   state = LowPriceTicketState.waiting_for_date_month_visited)
