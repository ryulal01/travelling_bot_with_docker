import re

from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from sqlalchemy.exc import IntegrityError

from app.models import User
from config.db import session


class RegistrationState(StatesGroup):
	waiting_for_name = State()
	waiting_for_age = State()


async def registration_start(message: types.Message, state: FSMContext):
	user_in_db = session.query(User).filter(
		User.user_id_tg == message.from_user.id).first()
	if user_in_db:
		await message.answer(
			f"Вы уже регистрировались прежде\n")
		await message.answer(
			f"""Ваши данные в системе:\n"""
			f"""Имя: {user_in_db.name}\n"""
			f"""Возраст: {user_in_db.age}"""
		)
		return
	await message.answer("Введите свое имя:")
	await state.set_state(RegistrationState.waiting_for_name.state)


async def name_given(message: types.Message, state: FSMContext):
	if not re.match("^[а-яА-ЯёЁ]+$", message.text):
		await message.answer(
			"Пожалуйста, введите кириллицей ваше имя")
		return

	await message.answer("Введите свой возраст:")
	await state.update_data(given_name = message.text.capitalize())

	await state.set_state(RegistrationState.waiting_for_age.state)


async def age_given(message: types.Message, state: FSMContext):
	if not message.text.isdigit():
		await message.answer(
			"Пожалуйста, введите цифрами ваш возраст")
		return
	age = int(message.text)
	if age > 99 or age < 6:
		await message.answer(
			"Пожалуйста, введите более реальный возраст")
		return

	user_data = await state.get_data()

	user_obj = User(
		user_id_tg = message.from_user.id,
		name = user_data['given_name'],
		age = age,
	)
	try:
		session.add(user_obj)
		session.commit()
	except IntegrityError as e:
		print(e)
		session.rollback()
		await message.answer(
			f"Вы уже регистрировались прежде\n")
		await state.finish()
	except Exception as e:
		print(e)
		session.rollback()
		await message.answer(
			f"Какой то сбой, попробуйте позже\n")
		await state.finish()
	else:
		await message.answer(
			f"Вы зарегистрировались под именем: {user_obj.name}!\n"
			f"Вы указали возраст: {user_obj.age}")
		await message.answer(
			f"Нажмите /start, чтобы посмотреть доступные вам команды")
		await state.finish()


def register_handlers_registration(dp: Dispatcher):
	dp.register_message_handler(registration_start, commands = "registration",
								state = "*")
	dp.register_message_handler(name_given,
								state = RegistrationState.waiting_for_name)
	dp.register_message_handler(age_given,
								state = RegistrationState.waiting_for_age)
