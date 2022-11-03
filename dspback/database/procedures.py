import sqlalchemy
from sqlalchemy.orm import Session

from dspback.database.models import AuthorTable, RepositorySubmissionTable, UserTable
from dspback.pydantic_schemas import RepositoryToken, RepositoryType, Submission


def submissions_report_json(db: Session):
    result_json = {}
    query = sqlalchemy.select([
        RepositorySubmissionTable.repo_type,
        sqlalchemy.func.count(RepositorySubmissionTable.repo_type)
    ]).group_by(RepositorySubmissionTable.repo_type)

    result = db.execute(query).fetchall()
    results = {}
    for i in result:
        results[i[0]] = i[1]

    result_json["submission_counts_by_repo"] = results
    query = sqlalchemy.select([sqlalchemy.func.count()]).select_from(RepositorySubmissionTable)
    total_submissions = db.execute(query).scalar()

    result_json["total_submissions"] = total_submissions
    return result_json


def create_or_update_submission(
    db: Session, submission: Submission, user: UserTable, metadata_json
) -> RepositorySubmissionTable:
    submission_row = (
        db.query(RepositorySubmissionTable)
        .filter(RepositorySubmissionTable.identifier == submission.identifier)
        .filter(RepositorySubmissionTable.user_id == user.id)
        .first()
    )
    if submission_row:
        db.delete(submission_row)

    db_repository_submission = RepositorySubmissionTable(
        title=submission.title,
        repo_type=submission.repo_type,
        identifier=submission.identifier,
        user_id=user.id,
        metadata_json=metadata_json,
        url=submission.url,
    )
    db.add(db_repository_submission)
    db.flush()
    for author in submission.authors:
        author = AuthorTable(name=author, repository_submission_id=db_repository_submission.id)
        db.add(author)

    db.commit()
    db.refresh(db_repository_submission)
    return db_repository_submission


def delete_submission(db: Session, repository: RepositoryType, identifier: str, user: UserTable):
    submission_row = (
        db.query(RepositorySubmissionTable)
        .filter(RepositorySubmissionTable.identifier == identifier)
        .filter(RepositorySubmissionTable.user_id == user.id)
        .filter(RepositorySubmissionTable.repo_type == repository)
        .first()
    )
    if submission_row:
        db.delete(submission_row)
    db.commit()


def delete_repository_access_token(db: Session, repository, user: UserTable):
    repository_token: RepositoryToken = user.repository_token(db, repository)
    if repository_token:
        db.delete(repository_token)
        db.commit()


def delete_access_token(db: Session, user: UserTable):
    user.access_token = None
    db.add(user)
    db.commit()
