from pymongo import MongoClient
from .config import Config

class MongoDB:

    def __init__(self, database,  collectionName):
        self.database = database
        self.collectionName = collectionName

    def initialize(self):
        client = MongoClient(Config.MONGO_URI)
        database = client[self.database]
        collection = database[self.collectionName]
        return collection
    
    def insert_one(self, record):
        collection = self.initialize()
        insert_one = collection.insert_one(record)
        return insert_one

    def insert_many(self, records):
        collection = self.initialize()
        collection.insert_many(records)

    def find_one(self, query):
        collection = self.initialize()
        record = collection.find_one(query)
        return record
    
    def find(self, query):
        collection = self.initialize()
        records = collection.find(query)
        return records
    
    def update_one(self, query, record):
        collection = self.initialize()
        update_one = collection.update_one(query, {"$set": record})
    
    def update_many(self, query, records):
        collection = self.initialize()
        update_many = collection.update_many(query, {"$set": records})
    
    def delete_one(self, query):
        collection = self.initialize()
        record = collection.delete_one(query)
        return record
    
    def delete_many(self, query):
        collection = self.initialize()
        record = collection.delete_many(query)
        return record
    
    def count_documents(self, query):
        collection = self.initialize()
        records_count = collection.count_documents(query)
        return records_count