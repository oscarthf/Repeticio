
import os
import logging

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

from ..obj.GlobalContainer import GlobalContainer

logger = logging.getLogger("language_app_backend.util.db")

def setup_globals():

    # check if globals have been set up already
    if "globals" in globals():
        logger.info("Globals already set up")
        return

    db_client = create_connection()
    success = test_connection(db_client)

    if not success:
        logger.error("Failed to connect to MongoDB")
        raise Exception("Failed to connect to MongoDB")
    
    global_container = GlobalContainer(db_client)
    
    globals()["global_container"] = global_container

def create_connection():

    connection_string = os.environ.get("LANGUAGE_APP_DB_CONNECTION_STRING")
    client = MongoClient(connection_string, server_api=ServerApi('1'))

    return client

def test_connection(client):

    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
        return True
    except Exception as e:
        print(e)
        return False