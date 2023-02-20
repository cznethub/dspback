
. ./.env

CONNECTION="${MONGO_PROTOCOL}://${MONGO_USERNAME}:${MONGO_PASSWORD}@${MONGO_HOST}/${MONGO_DATABASE}"

mongoimport --uri $CONNECTION --collection Submission --jsonArray repository_submission.json
mongoimport --uri $CONNECTION --collection RepositoryToken --jsonArray repository_token.json
mongoimport --uri $CONNECTION --collection User --jsonArray user.json