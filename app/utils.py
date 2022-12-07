from .models import MongoDB
from werkzeug.security import generate_password_hash
from .user import User
from datetime import datetime
from bson.objectid import ObjectId

users_col = MongoDB(database = "groupChat", collectionName = "users")
groups_col =  MongoDB(database = "groupChat", collectionName = "groups")
group_members =  MongoDB(database = "groupChat", collectionName = "members")
messages_col = MongoDB(database = "groupChat", collectionName = "messages")

class Authorization:
    """
    Schema for Authorization
    """
    def create_user(self, username, email, password):
        password_hash = generate_password_hash(password)
        user = users_col.insert_one(record = {"user_id":  username, 'email': email, 'password': password_hash, "created_at": datetime.now()})
    
    def get_user(self, username):
        user = users_col.find_one({"user_id": username})
        return User(user['user_id'], user['email'], user['password']) if user else None
    
    def update_user(self, username, email, password):
        password_hash = generate_password_hash(password)
        users_col.update_one(query = {"user_id": username}, record =  {"user_id":  username, 'email': email, 'password': password_hash, "modified_at": datetime.now()})
    
class Group:
    """
    Schema for Group
    """
    def create_group(self, group_name, created_by):
        group = groups_col.insert_one(record = {"group_name": group_name, "created_by": created_by, "created_at": datetime.now()})
        group_id = group.inserted_id
        self.add_group_member(group_id, group_name, created_by, created_by, is_admin=True)
        return group_id
    
    def add_group_member(self, group_id, group_name, username, added_by, is_admin=False):
        group_members.insert_one(record = {
            "_id": {
                "group_id": ObjectId(group_id),
                "username": username
            },
            "group_name": group_name,
            "added_by": added_by,
            "added_at": datetime.now(),
            "is_admin": is_admin
        })
    
    def add_group_members(self, group_id, group_name, usernames, added_by):
        group_members.insert_many(
            records = [{"_id": {"group_id": ObjectId(group_id),"username": username},"group_name": group_name, "added_by": added_by, "added_at": datetime.now(), "is_admin": False} for username in usernames]
            )

    def remove_group_members(self, group_id, usernames):
        group_members.delete_many({'_id': {'$in': [{'group_id': ObjectId(group_id), 'username': username} for username in usernames]}})

    def get_group_members(self, group_id):
        return list(group_members.find({"_id.group_id": ObjectId(group_id)}))

    def get_groups_of_user(self, username):
        return list(group_members.find({"_id.username": username}))
    
    def is_group_member(self, group_id, username):
        return group_members.count_documents({'_id': {'group_id': ObjectId(group_id), 'username': username}})

    def is_group_admin(self, group_id, username):
        return group_members.count_documents({'_id': {'group_id': ObjectId(group_id), 'username': username}, 'is_admin': True})

    def get_group(self, group_id):
        group = groups_col.find_one({"_id": ObjectId(group_id)})
        return group
    
    def update_group(self, group_id, group_name, username):
        groups_col.update_one(query = {'_id': ObjectId(group_id)}, record = {'group_name': group_name, "modified_at": datetime.now(), "modified_by": username})
        group_members.update_many({'_id.group_id': ObjectId(group_id)}, {'group_name': group_name})

    def remove_group(self, group_id):
        groups_col.delete_one(query = {"_id": ObjectId(group_id)})
        group_members.delete_many({"_id.group_id": ObjectId(group_id)})

class Message:
    """
    Schema for Message
    """
    def save_message(self, group_id, message, sender, created_at):
        message = messages_col.insert_one(record = {"group_id":  group_id, 'message': message, 'sender': sender, "created_at": created_at})
    
    def get_messages(self, group_id):
        messages =  list(messages_col.find({"group_id": group_id}))
        return messages
    
    def delete_messages(self, group_id):
        messages_col.delete_many(query = {"group_id": group_id})





    


    
    