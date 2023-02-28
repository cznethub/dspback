FROM mongo

COPY repository_submission.json repository_submission.json
COPY repository_token.json repository_token.json
COPY user.json user.json
COPY .env .env
COPY mongo_import.sh mongo_import.sh

RUN chmod +x mongo_import.sh

CMD ["/bin/sh", "mongo_import.sh"]