import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

POSTGRES_USER = os.environ.get('POSTGRES_USER')
POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_PORT = os.environ.get('DB_PORT')


engine = create_engine(
	f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")
Session = sessionmaker(autoflush = False, bind = engine)
session = Session()
