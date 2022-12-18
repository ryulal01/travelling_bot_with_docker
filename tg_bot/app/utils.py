import re

import requests
from aiogram import types

HEADERS = {
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
	'Accept-Encoding': 'gzip, deflate, br',
	'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7,it;q=0.6',
	'Cache-Control': 'max-age=0',
	'Connection': 'keep-alive',
	'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
	'sec-ch-ua-mobile': '?0',
	'sec-ch-ua-platform': '"Windows"',
	'Sec-Fetch-Dest': 'document',
	'Sec-Fetch-Mode': 'navigate',
	'Sec-Fetch-Site': 'same-origin',
	'Sec-Fetch-User': '?1',
	'Upgrade-Insecure-Requests': '1',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36',
}

DICT_MONTHS = (
	{'id': 1, 'name': 'Январь', 'name_id': 1},
	{'id': 2, 'name': 'Февраль', 'name_id': 2},
	{'id': 3, 'name': 'Март', 'name_id': 3},
	{'id': 4, 'name': 'Апрель', 'name_id': 4},
	{'id': 5, 'name': 'Май', 'name_id': 5},
	{'id': 6, 'name': 'Июнь', 'name_id': 6},
	{'id': 7, 'name': 'Июль', 'name_id': 7},
	{'id': 8, 'name': 'Август', 'name_id': 8},
	{'id': 9, 'name': 'Сентябрь', 'name_id': 9},
	{'id': 10, 'name': 'Октябрь', 'name_id': 10},
	{'id': 11, 'name': 'Ноябрь', 'name_id': 11},
	{'id': 12, 'name': 'Декабрь', 'name_id': 12}
)


def get_or_create(session, model, **kwargs):
	instance = session.query(model).filter_by(**kwargs).first()
	if instance:
		return instance
	else:
		try:
			instance = model(**kwargs)
			session.add(instance)
			session.commit()
		except Exception as e:
			print(e)
			session.rollback()
			return
		else:
			return instance


async def location_await_query_country_city(query: types.InlineQuery):
	term = query.query
	if not re.match("^[а-яА-ЯёЁ]+$", term) or len(term) < 1:
		return
	url = f'https://autocomplete.travelpayouts.com/places2?term={term}&locale=ru&types[]=city'
	r = requests.get(url = url, headers = HEADERS)
	response_json = r.json()

	results = [types.InlineQueryResultArticle(
		id = str(item_num.get('id')),
		title = f"Страна: {item_num.get('country_name')} | Город: {item_num.get('name')}",
		input_message_content = types.InputTextMessageContent(
			message_text = f"Страна: {item_num.get('country_name')} | Город: {item_num.get('name')}"
		),

	) for item_num in response_json]
	await query.answer(results[:10], is_personal = True,
					   next_offset = "")


async def location_await_query_code_country_city(query: types.InlineQuery):
	term = query.query
	if not re.match("^[а-яА-ЯёЁ]+$", term) or len(term) < 1:
		return
	url = f'https://autocomplete.travelpayouts.com/places2?term={term}&locale=ru&types[]=city'
	r = requests.get(url = url, headers = HEADERS)
	response_json = r.json()
	results = [types.InlineQueryResultArticle(
		id = str(item_num.get('id')),
		title = f"{item_num.get('country_name')}, {item_num.get('name')} | Код : {item_num.get('code')}",
		input_message_content = types.InputTextMessageContent(
			message_text = f"{item_num.get('country_name')}, {item_num.get('name')} | Код : {item_num.get('code')}"
		),

	) for item_num in response_json]
	await query.answer(results[:10], is_personal = True,
					   next_offset = "")
