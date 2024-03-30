import os
import yaml
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class DBConfig:
    def __init__(self, user, password, hostname, port, database):
        self.user = user
        self.password = password
        self.hostname = hostname
        self.port = port
        self.database = database

    def __repr__(self):
        return f"<DBConfig {self.user} {self.hostname} {self.port} {self.database}>"

    def __str__(self):
        return f"<DBConfig {self.user} {self.hostname} {self.port} {self.database}>"


with open("whatsnext/dbconfig.yaml", "r") as f:
    db = yaml.load(f, Loader=yaml.FullLoader)
    db = DBConfig(**db)

SQLALCHEMY_DATABASE_URL = f"postgresql://{db.user}:{db.password}@{db.hostname}:{db.port}/{db.database}"

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
