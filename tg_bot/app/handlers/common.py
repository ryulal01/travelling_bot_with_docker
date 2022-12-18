from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext

from app.models import User
from config.db import session


async def cmd_start(message: types.Message, state: FSMContext):
	await state.finish()

	user_in_db = session.query(User).filter(
		User.user_id_tg == message.from_user.id).first()
	if not user_in_db:
		await message.answer(
			"Вы в начальном меню!\n"
			"У вас ограниченный доступ\n"
			"Вы можете:\n"
			"посмотреть последние комментарии в системе: /find_last_comments\n"
			"посмотреть дешевый авиабилет: /find_low_price_avia_tickets\n"
			"выйти из диалога:  /cancel\n"
			"Для полного доступа пройдите регистрацию, нажав:\n /registration",
			reply_markup = types.ReplyKeyboardRemove()
		)
		return
	await message.answer(
		"Вы в начальном меню!\n"
		"У вас полный доступ и можете:\n"
		"оставить комментарий, о городе: /create_comment_city\n"
		"посмотреть дешевый авиабилет: /find_low_price_avia_tickets\n"
		"посмотреть комментарии, о городе: /find_comments_by_city\n"
		"посмотреть последние комментарии в системе: /find_last_comments\n"
		"выйти из диалога: /cancel\n",
		reply_markup = types.ReplyKeyboardRemove()
	)


async def cmd_cancel(message: types.Message, state: FSMContext):
	await state.finish()
	await message.answer("Вы окончили предыдущий диалог",
						 reply_markup = types.ReplyKeyboardRemove())


def register_handlers_common(dp: Dispatcher):
	dp.register_message_handler(cmd_start, commands = "start", state = "*")
	dp.register_message_handler(cmd_cancel, commands = "cancel", state = "*")

