from db import Base, engine

def init_db_if_needed():
    Base.metadata.create_all(bind=engine)