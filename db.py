from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine.url import URL
import os
from dotenv import load_dotenv

load_dotenv()

# DB_CONFIG = {
#     "drivername" : "postgresql+psycopg2",
#     "database": os.getenv("DB_NAME"),
#     "username": os.getenv("DB_USER"),
#     "password": os.getenv("DB_PASSWORD"),
#     "host": os.getenv("DB_HOST"),
#     "port": os.getenv("DB_PORT"),
# }

DATABASE_URL = os.environ.get("DATABASE_URL")

# To switch to Neon database for deployment
engine = create_engine(DATABASE_URL, echo=True)

# engine = create_engine(URL.create(**DB_CONFIG), echo=True)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()