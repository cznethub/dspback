from dspback.database.models import RepositorySubmissionTable, AuthorTable


def create_submission(db, submission, user):
    db_repository_submission = RepositorySubmissionTable(title=submission.title, repo_type=submission.repo_type,
                                                         status=submission.status, identifier=submission.identifier,
                                                         user_id=user.id)
    db.add(db_repository_submission)
    db.flush()
    for author in submission.authors:
        author = AuthorTable(name=author, repository_submission_id=db_repository_submission.id)
        db.add(author)

    db.commit()
    db.refresh(db_repository_submission)
    return db_repository_submission
