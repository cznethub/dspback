from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, BigInteger, create_engine, DateTime
from sqlalchemy.orm import relationship, DeclarativeMeta, declarative_base, sessionmaker
from sqlalchemy.sql import func

from dspback.config import DATABASE_URL


engine = create_engine(
    DATABASE_URL
)

Base: DeclarativeMeta = declarative_base()


class UserTable(Base):
    """Base SQLAlchemy users table definition."""
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    name = Column(String(length=64), nullable=False)
    # email = Column(String(length=64), nullable=False)
    orcid = Column(String(length=64), nullable=False)
    access_token = Column(String(length=64), nullable=False)
    refresh_token = Column(String(length=128), nullable=True)
    expires_in = Column(BigInteger, nullable=True)
    expires_at = Column(BigInteger, nullable=True)
    repository_tokens = relationship("RepositoryTokenTable")
    submissions = relationship("RepositorySubmissionTable")


class RepositoryTokenTable(Base):
    """Base SQLAlchemy repository token table definition."""

    __tablename__ = "repository_token"

    id = Column(Integer, primary_key=True)
    type = Column(String(length=64), nullable=False)
    access_token = Column(String(length=128), nullable=False)
    repo_user_id = Column(String(length=64), nullable=True)
    refresh_token = Column(String(length=128), nullable=True)
    expires_in = Column(BigInteger, nullable=True)
    expires_at = Column(BigInteger, nullable=True)
    user_id = Column(Integer, ForeignKey('user.id'))


class AuthorTable(Base):
    """Base SQLAlchemy author table definition."""

    __tablename__ = "author"

    id = Column(Integer, primary_key=True)
    name = Column(String(), nullable=False)
    repository_submission_id = Column(Integer, ForeignKey('repository_submission.id'))


class RepositorySubmissionTable(Base):
    """Base SQLAlchemy repository submission table definition."""

    __tablename__ = "repository_submission"

    id = Column(Integer, primary_key=True)
    title = Column(String(), nullable=False)
    authors = relationship("AuthorTable")
    repo_type = Column(String(length=64), nullable=False)
    status = Column(String(length=32), nullable=False)
    identifier = Column(String(), nullable=False)
    submitted = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('user.id'))


Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
