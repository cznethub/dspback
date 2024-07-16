# Postgres to Mongo Migration steps

1. After a new deployment, login to the db-0*-czn VM
2. Download these files to a temporary directory:
    * wget https://raw.githubusercontent.com/cznethub/dspback/mongo_migration/migrations/postgres_to_mongodb/Dockerfile
    * wget https://raw.githubusercontent.com/cznethub/dspback/mongo_migration/migrations/postgres_to_mongodb/mongo_import.sh
    * wget https://raw.githubusercontent.com/cznethub/dspback/mongo_migration/migrations/postgres_to_mongodb/postgres_dump.sh
3. Copy the .env file to the temporary directory
    * cp /projects/cznethub/dsp/targets/{environment}/.env .env
4. Run the postgres database dump
    * chmod +x postgres_dump.sh
    * ./postgres_dump.sh
5. From the temporary directory, build the Dockerfile
    * docker build -t mongoimport .
6. From the temporary directory, run the newly built docker image
    * docker run --name mongoimport mongoimport
7. Cleanup
    * Delete the temporary directory
    * docker rm mongoimport
    * docker rmi $(docker images 'mongoimport' -a -q)
8. Login to backend-0*-czn VM
    * build a uri for the environment from `mongodb+srv://{username}:{password}@cluster0.iouzjvv.mongodb.net` 
    * docker exec dspback beanie migrate -uri {your_uri_here} -db 'czo_{env}' -p migrations --distance 1
