import sqlalchemy
import pytest


database = sqlalchemy.create_engine('postgresql://username:password@database:5432/default_database')

@pytest.fixture()
def db():
    database.execute("DROP TABLE IF EXISTS testing")
    database.execute("CREATE TABLE testing (id integer PRIMARY KEY, name varchar(40));")
    yield database
    database.execute("DROP TABLE IF EXISTS testing")

def test_the_db(db):
    db.execute("INSERT INTO testing (id, name) VALUES (100, 'testingvarchar')")
    result_set = db.execute("SELECT * FROM testing")
    for (r) in result_set:
        assert r[0] == 100
        assert r[1] == 'testingvarchar'