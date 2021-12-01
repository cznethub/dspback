from sqlalchemy.orm import Session

from dspback.database.models import AuthorTable, RepositorySubmissionTable, UserTable
from dspback.schemas import Submission


def create_or_update_submission(db: Session, submission: Submission, user: UserTable) -> RepositorySubmissionTable:
    submission_row = (
        db.query(RepositorySubmissionTable)
        .filter(RepositorySubmissionTable.identifier == submission.identifier)
        .first()
    )
    if submission_row:
        db.delete(submission_row)

    db_repository_submission = RepositorySubmissionTable(
        title=submission.title,
        repo_type=submission.repo_type,
        status=submission.status,
        identifier=submission.identifier,
        user_id=user.id,
    )
    db.add(db_repository_submission)
    db.flush()
    for author in submission.authors:
        author = AuthorTable(name=author, repository_submission_id=db_repository_submission.id)
        db.add(author)

    db.commit()
    db.refresh(db_repository_submission)
    return db_repository_submission
