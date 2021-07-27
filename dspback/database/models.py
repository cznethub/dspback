from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger
from sqlalchemy.orm import relationship

from backend.database import Base


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