import databases
import sqlalchemy
from fastapi_users import models, FastAPIUsers
from fastapi_users.authentication import CookieAuthentication
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import relationship


Base: DeclarativeMeta = declarative_base()

DATABASE_URL = 'postgresql://username:password@database:5432/default_database'

database = databases.Database(DATABASE_URL)


class User(models.BaseUser):
    pass

class UserCreate(models.BaseUserCreate):
    pass

class UserUpdate(User, models.BaseUserUpdate):
    pass

class UserDB(User, models.BaseUserDB):
    pass

class UserTable(Base, SQLAlchemyBaseUserTable):
    repositories = relationship("Repository", back_populates="repository")

class Repository(Base):
    """Base SQLAlchemy users table definition."""

    __tablename__ = "repository"

    id = Column(Integer, primary_key=True)
    type = Column(String(length=64), nullable=False)
    repo_user_id = Column(String(length=64), nullable=False)
    access_token = Column(String(length=128), nullable=False)
    refresh_token = Column(String(length=128), nullable=False)

    users = relationship("UserTable", back_populates="user")


users = UserTable.__table__





SECRET = "SECRET"
cookie_authentication = CookieAuthentication(
    secret=SECRET, lifetime_seconds=3600
)

user_db = SQLAlchemyUserDatabase(UserDB, database, users)

fastapi_users = FastAPIUsers(
    user_db,
    [cookie_authentication],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)



engine = sqlalchemy.create_engine(
    DATABASE_URL
)

Base.metadata.create_all(engine)
