import sqlalchemy
import pytest

from ..db import database


@pytest.fixture()
@pytest.mark.asyncio
async def db():
    await database.execute("DROP TABLE IF EXISTS testing")
    await database.execute("CREATE TABLE testing (id integer PRIMARY KEY, name varchar(40));")
    yield database
    await database.execute("DROP TABLE IF EXISTS testing")

@pytest.mark.asyncio
async def test_the_db(db):
    await db.execute("INSERT INTO testing (id, name) VALUES (100, 'testingvarchar')")
    result_set = await db.execute("SELECT * FROM testing")
    for (r) in result_set:
        assert r[0] == 100
        assert r[1] == 'testingvarchar'