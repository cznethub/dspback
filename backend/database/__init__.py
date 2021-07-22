from enum import Enum
from typing import List, Optional

import databases
import sqlalchemy
from fastapi_users import models, FastAPIUsers
from fastapi_users.authentication import CookieAuthentication
from fastapi_users.db import SQLAlchemyBaseUserTable, SQLAlchemyUserDatabase
from fastapi_users.db.sqlalchemy import SQLAlchemyBaseOAuthAccountTable
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import relationship
from pydantic import UUID4, BaseModel


Base: DeclarativeMeta = declarative_base()

DATABASE_URL = 'postgresql://username:password@database:5432/default_database'

database = databases.Database(DATABASE_URL)

class StringEnum(str, Enum):
    pass

class TypeEnum(StringEnum):
    ZENODO = "zenodo"
    ORCID = "orcid"
    HYDROSHARE = "hydroshare"

class Repository(BaseModel):
    id: UUID4 = None
    type: TypeEnum = TypeEnum.ORCID
    access_token: str = None
    repo_user_id: Optional[str] = None
    refresh_token: Optional[str] = None

class RepositoryCreate(BaseModel):
    type: TypeEnum = TypeEnum.ORCID
    access_token: str = None
    repo_user_id: Optional[str] = None
    refresh_token: Optional[str] = None

class User(models.BaseUser, models.BaseOAuthAccountMixin):
    repositories: List[Repository] = None

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
    access_token = Column(String(length=128), nullable=False)
    repo_user_id = Column(String(length=64), nullable=True)
    refresh_token = Column(String(length=128), nullable=True)

class OAuthAccount(SQLAlchemyBaseOAuthAccountTable, Base):
    pass


SECRET = "SECRET"
cookie_authentication = CookieAuthentication(
    secret=SECRET, lifetime_seconds=3600
)

user_db = SQLAlchemyUserDatabase(UserDB, database, UserTable.__table__, OAuthAccount.__table__)

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
