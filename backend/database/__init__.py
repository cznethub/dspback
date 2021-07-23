from enum import Enum
from typing import List, Optional

#import databases
import sqlalchemy
from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import DeclarativeMeta, declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from pydantic import UUID4, BaseModel, EmailStr

Base: DeclarativeMeta = declarative_base()

DATABASE_URL = 'postgresql://username:password@database:5432/default_database'

#database = databases.Database(DATABASE_URL)

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    orcid: Optional[str] = None

class StringEnum(str, Enum):
    pass

class Repo(StringEnum):
    ZENODO = "zenodo"
    HYDROSHARE = "hydroshare"

class ORCIDResponse(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    expires_in: int
    scope: str
    name: str
    orcid: str
    id_token: str
    expires_at: str

class RepositoryBase(BaseModel):
    id: UUID4 = None
    repo: Repo = None
    access_token: str = None
    repo_user_id: Optional[str] = None
    refresh_token: Optional[str] = None

class Repository(RepositoryBase):

    class Config:
        orm_mode = True

class UserBase(BaseModel):
    id: Optional[UUID4] = None
    name: str = None
    #email: EmailStr = None
    orcid: str = None
    access_token: str = None
    refresh_token: str = None
    expires_in: int = None
    expires_at: int = None
    repositories: List[Repository] = None

class User(UserBase):

    class Config:
        orm_mode = True

class UserTable(Base):

    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(length=64), nullable=False)
    #email = Column(String(length=64), nullable=False)
    orcid = Column(String(length=64), nullable=False)
    access_token = Column(String(length=64), nullable=False)
    refresh_token = Column(String(length=128), nullable=True)
    expires_in = Column(BigInteger, nullable=True)
    expires_at = Column(BigInteger, nullable=True)
    repositories = relationship("RepositoryTable")

class RepositoryTable(Base):
    """Base SQLAlchemy users table definition."""

    __tablename__ = "repository"

    id = Column(Integer, primary_key=True)
    type = Column(String(length=64), nullable=False)
    access_token = Column(String(length=128), nullable=False)
    repo_user_id = Column(String(length=64), nullable=True)
    refresh_token = Column(String(length=128), nullable=True)
    user_id = Column(Integer, ForeignKey('user.id'))


SECRET = "SECRET"

engine = sqlalchemy.create_engine(
    DATABASE_URL
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(engine)
