from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeMeta, Session, declarative_base, relationship, sessionmaker

from dspback.config import DATABASE_URL
from dspback.schemas import RepositoryType

engine = create_engine(DATABASE_URL)

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

    def repository_token(self, db: Session, repository: RepositoryType):
        repo_type = repository.value
        return (
            db.query(RepositoryTokenTable)
            .filter(RepositoryTokenTable.user_id == self.id, RepositoryTokenTable.type == repo_type)
            .first()
        )


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
    identifier = Column(String(), nullable=False)
    title = Column(String(), nullable=False)
    authors = relationship("AuthorTable", order_by=AuthorTable.id, cascade="all, delete, delete-orphan")
    repo_type = Column(String(length=64), nullable=False)
    submitted = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('user.id'))

    UniqueConstraint('identifier')


Base.metadata.create_all(engine)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
