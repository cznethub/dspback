from fastapi_users import models, FastAPIUsers
from fastapi_users.authentication import JWTAuthentication
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from backend.db import database, engine
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base


class User(models.BaseUser):
    pass


class UserCreate(models.BaseUserCreate):
    pass


class UserUpdate(User, models.BaseUserUpdate):
    pass


class UserDB(User, models.BaseUserDB):
    pass


Base: DeclarativeMeta = declarative_base()

class UserTable(Base, SQLAlchemyBaseUserTable):
    pass

Base.metadata.create_all(engine)

users = UserTable.__table__
user_db = SQLAlchemyUserDatabase(UserDB, database, users)

SECRET = "SECRET"
jwt_authentication = JWTAuthentication(
    secret=SECRET, lifetime_seconds=3600, tokenUrl="/api/auth/jwt/login"
)

fastapi_users = FastAPIUsers(
    user_db,
    [jwt_authentication],
    User,
    UserCreate,
    UserUpdate,
    UserDB,
)
