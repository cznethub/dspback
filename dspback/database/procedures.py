from motor.motor_asyncio import AsyncIOMotorCollection as Session

from dspback.pydantic_schemas import RepositoryType, User, Submission

async def create_or_update_submission(
    db: Session, submission: Submission, user: User) -> Submission:
    await db["repository_submission"].replace_one({"identifier": submission.identifier, "user_id": user.id}, submission.dict(), True)

    return submission


async def delete_submission(db: Session, repository: RepositoryType, identifier: str, user: User):
    await db["repository_submission"].delete_one({"identifier": identifier, "user_id": user.id, "repo_type": repository})


async def delete_repository_access_token(db: Session, repository, user: User):
    del user.repository_tokens[repository]
    await db["repository_token"].update_one(user.dict())


async def delete_access_token(db: Session, user: User):
    user.access_token = None
    await db["user"].update_one(user.dict())
