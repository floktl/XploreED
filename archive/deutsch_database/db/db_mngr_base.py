from abc import ABC, abstractmethod

class BaseDBManager(ABC):
    def __init__(self, db_connection):
        self.db = db_connection

    def connect(self):
        print("Connecting to database...")

    def disconnect(self):
        print("Disconnecting from database...")

    @abstractmethod
    def insert(self, data):
        pass

    @abstractmethod
    def find(self, query):
        pass

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.disconnect()