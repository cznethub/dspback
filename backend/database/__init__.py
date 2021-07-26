import sqlalchemy
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base

DATABASE_URL = 'postgresql://username:password@database:5432/default_database'

engine = sqlalchemy.create_engine(
    DATABASE_URL
)

Base: DeclarativeMeta = declarative_base()
Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
