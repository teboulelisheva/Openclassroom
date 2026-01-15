from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+psycopg2://openpg:openpgpwd@localhost:5432/energy_ml"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
