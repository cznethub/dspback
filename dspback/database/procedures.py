from beanie import DeleteRules

from dspback.pydantic_schemas import User
from dspback.utils.mongo import delete_jsonld


async def delete_submission(identifier: str, user: User):
    await user.fetch_link(User.submissions)
    submission = user.submission(identifier)
    submission.delete(link_rule=DeleteRules.DELETE_LINKS)
    delete_jsonld(identifier)


async def delete_repository_access_token(repository, user: User):
    await user.fetch_link(User.repository_tokens)
    repository_token = user.repository_token(repository)
    repository_token.delete(link_rule=DeleteRules.DELETE_LINKS)
