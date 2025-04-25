
class GlobalContainer:
    __slots__ = ("db_client", "db")
    def __init__(self, db_client):
        self.db_client = db_client
        self.db = db_client.get_database("language_app")
        