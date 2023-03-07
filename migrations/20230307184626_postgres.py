from beanie import free_fall_migration, WriteRules
from pydantic import Field

from dspback.pydantic_schemas import User, Submission, RepositoryToken

class UserOld(User):
    old_id: int = Field(alias="id", default=None)

    class Settings:
        name = "User"

class SubmissionOld(Submission):
    user_id: int = None

    class Settings:
        name = "Submission"

class RepositoryTokenOld(RepositoryToken):
    user_id: int = None

    class Settings:
        name = "RepositoryToken"

class Forward:
    @free_fall_migration(document_models=[UserOld, User, SubmissionOld, Submission, RepositoryTokenOld, RepositoryToken])
    async def link_users_submissions_and_repotokens(self, session):
        async for submission_old in SubmissionOld.find_all():
            if submission_old.user_id:
                user_old = await UserOld.find_one(UserOld.old_id == submission_old.user_id)
                submission = Submission(**submission_old.dict())
                user_old.submissions.append(submission)
                await user_old.save(link_rule=WriteRules.WRITE)
            else:
                print(f"Could not link user to {submission_old}")

        async for repository_token_old in RepositoryTokenOld.find_all():
            if repository_token_old.user_id:
                user_old = await UserOld.find_one(UserOld.old_id == repository_token_old.user_id)
                repository_token = RepositoryToken(**repository_token_old.dict())
                user_old.repository_tokens.append(repository_token)
                await user_old.save(link_rule=WriteRules.WRITE)
            else:
                print(f"Could not link user to {repository_token_old}")
