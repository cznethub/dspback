from pymongo import MongoClient


def get_database():

    # Provide the mongodb atlas url to connect python to mongodb using pymongo
    CONNECTION_STRING = "mongodb+srv://user:password@cluster0.iouzjvv.mongodb.net/?retryWrites=true&w=majority"

    # Create a connection using MongoClient. You can import MongoClient or use pymongo.MongoClient
    client = MongoClient(CONNECTION_STRING, tls=True, tlsAllowInvalidCertificates=True)

    # Create the database for our example (we will use the same database throughout the tutorial
    return client['czo']['test_cznet']


def upsert_jsonld(json_ld):
    collection = get_database()
    id_filter = {'@id': json_ld['@id']}
    collection.update_one(id_filter, {'$set': json_ld}, upsert=True)
