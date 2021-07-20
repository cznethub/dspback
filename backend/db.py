import databases
import sqlalchemy

DATABASE_URL = 'postgresql://username:password@database:5432/default_database'

database = databases.Database(DATABASE_URL)

engine = sqlalchemy.create_engine(
    DATABASE_URL
)