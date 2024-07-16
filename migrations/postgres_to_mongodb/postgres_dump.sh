docker exec -u postgres database psql -U cznuser cznethubdb -c " SELECT row_to_json(u) FROM (SELECT * FROM repository_submission) u;" > repository_submission.json
sed -i '1d' repository_submission.json
sed -i '1d' repository_submission.json
sed -i '$d' repository_submission.json
sed -i '$d' repository_submission.json
sed -i s/$/,/ repository_submission.json
sed -i '1i [' repository_submission.json
sed -i '$s/,$/]/' repository_submission.json

docker exec -u postgres database psql -U cznuser cznethubdb -c " SELECT row_to_json(u) FROM (SELECT * FROM repository_token) u;" > repository_token.json
sed -i '1d' repository_token.json
sed -i '1d' repository_token.json
sed -i '$d' repository_token.json
sed -i '$d' repository_token.json
sed -i s/$/,/ repository_token.json
sed -i '1i [' repository_token.json
sed -i '$s/,$/]/' repository_token.json

docker exec -u postgres database psql -U cznuser cznethubdb -c " SELECT row_to_json(u) FROM (SELECT * FROM \"user\") u;" > user.json
sed -i '1d' user.json
sed -i '1d' user.json
sed -i '$d' user.json
sed -i '$d' user.json
sed -i s/$/,/ user.json
sed -i '1i [' user.json
sed -i '$s/,$/]/' user.json
