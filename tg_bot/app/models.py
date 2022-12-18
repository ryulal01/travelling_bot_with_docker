from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, \
	ForeignKey, UniqueConstraint, event
from sqlalchemy.orm import declarative_base, relationship

from config.db import engine

Base = declarative_base()


class User(Base):
	__tablename__ = 'users'
	id = Column(Integer, primary_key = True)
	created_on = Column(DateTime(), default = datetime.now)
	updated_on = Column(DateTime(), default = datetime.now,
						onupdate = datetime.now)
	user_id_tg = Column(Integer, unique = True, nullable = False)
	age = Column(Integer, nullable = False)
	name = Column(String(50), nullable = False)

	user_visited = relationship("UserVisited", backref = "user")


class CityCountry(Base):
	__tablename__ = 'cities_countries'
	id = Column(Integer, primary_key = True)
	created_on = Column(DateTime(), default = datetime.now)
	updated_on = Column(DateTime(), default = datetime.now,
						onupdate = datetime.now)
	city_name = Column(String(50), unique = True, nullable = False)
	country_name = Column(String(50), nullable = False)
	user_visited = relationship("UserVisited", backref = "country")

	__table_args__ = (
		UniqueConstraint(
			'city_name',
			'country_name',
			name = 'country_city_unique'),
	)


class Month(Base):
	__tablename__ = 'months'
	id = Column(Integer, primary_key = True)
	name = Column(String(50), unique = True, nullable = False)
	name_id = Column(Integer, unique = True, nullable = False)
	user_visited = relationship("UserVisited", backref = "month")

	__table_args__ = (
		UniqueConstraint(
			'name',
			'name_id',
			name = 'name_order_id_month'),
	)


class UserVisited(Base):
	__tablename__ = 'user_visited'
	id = Column(Integer, primary_key = True)
	created_on = Column(DateTime(), default = datetime.now)
	updated_on = Column(DateTime(), default = datetime.now,
						onupdate = datetime.now)

	month_rel = Column(Integer, ForeignKey('months.id'))
	voted = Column(Integer, nullable = False)
	comment_visited = Column(String(250), nullable = False)
	user_rel = Column(Integer, ForeignKey('users.id'))
	country_rel = Column(Integer, ForeignKey('cities_countries.id'))

	__table_args__ = (
		UniqueConstraint(
			'user_rel',
			'country_rel',
			name = 'user_city_unique'),
	)


Base.metadata.create_all(bind = engine)
