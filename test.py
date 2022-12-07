import requests
import unittest
import random
import string
from app.routes import app
from flask_login import current_user
from app.models import MongoDB
from app.utils import Authorization

letters = string.ascii_lowercase
username = ''.join(random.choice(letters) for i in range(10))
email = username+"@gmail.com"
password = username
new_password = ''.join(random.choice(letters) for i in range(10))

MongoDB(database = "groupChat", collectionName = "users").delete_many(query = {"user_id": "Susan"})
MongoDB(database = "groupChat", collectionName = "users").delete_many(query = {"user_id": "Mark"})
MongoDB(database = "groupChat", collectionName = "groups").delete_many(query ={"created_by":"Susan"})
MongoDB(database = "groupChat", collectionName = "members").delete_many(query= {"added_by": "Susan"})
Authorization().create_user("Susan", "Susan@gmail.com", "Susan123")
Authorization().create_user("Mark", "Mark@gmail.com", "Mark123")

class TestApi(unittest.TestCase):

    def setUp(self):
        self.client = app.test_client()
    
    def login(self):
        self.client.post('/login', data={
            'username': 'Susan',
            'password': 'Susan123',
        })

    def test_registration_form(self):
        response = self.client.get('/authorization')
        assert response.status_code == 200
        html = response.get_data(as_text=True)

        # make sure all the fields are included
        assert 'name="username"' in html
        assert 'name="email"' in html
        assert 'name="password"' in html
        assert 'type="submit"' in html
    
    def test_register_user(self):
        response = self.client.post('/signup', data={
            'username': username,
            'email': email,
            'password': password,
        }, follow_redirects=True)
        assert response.status_code == 200
        assert response.request.path == '/login' # redirected to login


        # user login
        response = self.client.post('/login', data={
            'username': username,
            'password': password,
        }, follow_redirects=True)
        assert response.status_code == 200
        html = response.get_data(as_text = True)
        assert 'Hi {}'.format(username)
        
        # user logout
        response = self.client.get('/logout', follow_redirects=True)
        assert response.status_code == 200

    def test_create_group_api(self):
        self.login()
        group_name = "test"
        response = self.client.post('/create-group', data={
           'group_name': group_name, 
           'members': "Mark"
        }, follow_redirects=True)
        assert response.status_code == 200
        html = response.get_data(as_text = True)
        assert "test Group" in html
        return group_name
    
    def test_edit_group(self):
        group_name = self.test_create_group_api()
        group = MongoDB(database = "groupChat", collectionName = "members").find_one(query ={"group_name": group_name})
        path = "/groups/{}/update".format(str(group['_id']['group_id']))
        response =  self.client.post(path, data={
           'group_name':"test1", 
           'members': "Susan,Mark"
        }, follow_redirects=True)
        assert response.status_code == 200
        return str(group['_id']['group_id'])

    def test_delete_group(self):
        group_id = self.test_edit_group()
        path = "/groups/{}/delete".format(group_id)
        response =  self.client.get(path, follow_redirects=True)
        assert response.status_code == 200

   

if __name__ == '__main__':
    unittest.main()