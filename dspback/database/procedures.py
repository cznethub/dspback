from beanie import DeleteRules

from dspback.pydantic_schemas import User


async def delete_submission(identifier: str, user: User):
    submission = user.submission(identifier)
    submission.delete(link_rule=DeleteRules.DELETE_LINKS)


async def delete_repository_access_token(repository, user: User):
    repository_token = user.repository_token(repository)
    repository_token.delete(link_rule=DeleteRules.DELETE_LINKS)
