import asyncio
import sys

import motor
from beanie import WriteRules, init_beanie

from dspback.config import get_settings
from dspback.pydantic_schemas import User, RepositoryToken, Submission

'''
This python script takes two parameters, the orcid for the from_user followed by the orcid for the to_user.
All submissions from the first user are transferred to the second user.

Example call:

docker exec dspback python management/transfer_submissions.py 0009-0005-8262-8321 0000-0002-1051-8511
'''

async def initiaize_beanie():
    db = motor.motor_asyncio.AsyncIOMotorClient(get_settings().mongo_url)
    await init_beanie(
        database=db[get_settings().mongo_database], document_models=[User, Submission, RepositoryToken]
    )

async def main():
    await initiaize_beanie()

    from_user_orcid = sys.argv[1]
    to_user_orcid = sys.argv[2]

    from_user = await User.find_one(User.orcid == from_user_orcid)
    if not from_user:
        print(f"Could not find user with {from_user_orcid}")
        return
    await from_user.fetch_all_links()
    to_user = await User.find_one(User.orcid == to_user_orcid)
    if not to_user:
        print(f"Could not find user with {to_user_orcid}")
        return
    await to_user.fetch_all_links()

    to_user.submissions.extend(from_user.submissions)
    from_user.submissions.clear()

    await to_user.save(link_rule=WriteRules.WRITE)
    await from_user.save(link_rule=WriteRules.WRITE)


if __name__ == "__main__":
    asyncio.run(main())