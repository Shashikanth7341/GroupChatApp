from flask import Flask, request, jsonify, session, render_template, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, SocketIO, join_room, leave_room, emit
from flask_login import LoginManager, current_user, login_user, login_required, logout_user
from .utils import Authorization, Group, Message
from datetime import datetime
from pymongo import DESCENDING

app = Flask(__name__)
app.secret_key = "my secret key"
socketio = SocketIO(app)
login_manager = LoginManager()
login_manager.login_view = 'user_login'
login_manager.init_app(app)

@app.route("/")
def home_page():
    return render_template("index.html")

@app.route("/authorization")
def main_page():
    return render_template("login_registration.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('home_page'))

    message = ''
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        user = Authorization().get_user(username)
        if user: 
            message = "Username already exists"
            return render_template('login_registration.html', message=message)

        Authorization().create_user(username, email, password)
        return redirect(url_for('user_login'))
    return render_template('login_registration.html', message=message)


@app.route("/login", methods= ["GET","POST"])
def user_login():
    if current_user.is_authenticated:
        return redirect(url_for('create_group'))

    message_log = ''
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = Authorization().get_user(username)
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('create_group'))
        else:
            message_log = 'Username or Password is Wrong!'
            
    return render_template('login_registration.html', message=message_log)

@app.route("/users/<username>", methods=["GET","POST"])
@login_required
def edit_user(username):
    user = Authorization().get_user(username)
    message = ''
    if request.method == 'POST':
        new_password = request.form.get('password')
        if user:
             Authorization().update_user(username, user.email, new_password)
             return redirect(url_for('logout'))
    return render_template('edit_user.html', user=user.__dict__, message=message)

@app.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for('main_page'))

@app.route("/create-group/", methods= ["GET","POST"])
@login_required
def create_group():
    message = ''
    if request.method == 'POST':
        group_name = request.form.get('group_name')
        usernames = []
        print(group_name)
        for username in request.form.get('members').split(','):
            if Authorization().get_user(username.strip()):
                usernames.append(username.strip())
            else: 
                message = "Username {} not Found".format(username.strip())
                return render_template('create_group.html', message=message, username = current_user.username)
        if len(group_name) and len(usernames):
            group_id = Group().create_group(group_name, current_user.username)
            if current_user.username in usernames:
                usernames.remove(current_user.username)
            Group().add_group_members(group_id, group_name, usernames, current_user.username)
            return redirect(url_for('view_group', group_id=group_id))
        else:
            message = "Failed to create group"
    return render_template('create_group.html', message=message, username = current_user.username)

@app.route('/groups/<group_id>/update', methods=['GET', 'POST'])
@login_required
def modify_room(group_id):
    group = Group().get_group(group_id)
    if group and Group().is_group_admin(group_id, current_user.username):
        existing_group_members = [member['_id']['username'] for member in Group().get_group_members(group_id)]
        group_members_str = ",".join(existing_group_members)
        message = ''
        if request.method == 'POST':
            group_name = request.form.get('group_name')
            group['group_name'] = group_name
            Group().update_group(group_id, group_name, current_user.username)
            
            new_members = []
            for username in request.form.get('members').split(','):
                if Authorization().get_user(username.strip()):
                    new_members.append(username.strip())
                else: 
                    message = "Username {} not Found".format(username.strip())
                    return render_template('edit_group.html', group=group, group_members_str=group_members_str, message=message)
            members_to_add = list(set(new_members) - set(existing_group_members))
            members_to_remove = list(set(existing_group_members) - set(new_members))
            if len(members_to_add):
                Group().add_group_members(group_id, group_name, members_to_add, current_user.username)
            if len(members_to_remove):
                Group().remove_group_members(group_id, members_to_remove)
            message = 'Group edited successfully'
            group_members_str = ",".join(new_members)
        return render_template('edit_group.html', group=group, group_members_str=group_members_str, message=message)
    else:
        return "You are not Admin", 404

@app.route('/groups/<group_id>/delete')
@login_required
def delete_group(group_id):
    group = Group().remove_group(group_id)
    Message().delete_messages(group_id)
    return redirect(url_for('list_groups'))

@app.route("/groups")
@login_required
def list_groups():
    groups = []
    for group in Group().get_groups_of_user(current_user.username):
        groups.append(group)
    return render_template('view_groups.html', groups=groups, username = current_user.username)

@app.route('/groups/<group_id>/')
@login_required
def view_group(group_id):
    group = Group().get_group(group_id)
    if group and Group().is_group_member(group_id, group['created_by']):
        group_members = Group().get_group_members(group_id)
        group_messages = Message().get_messages(group_id)
        return render_template('group_chat.html', username=current_user.username, group=group, group_members=group_members, group_messages = group_messages)
    else:
        return "Group not found", 404

@socketio.on('join_group')
def join_group_event(data):
    app.logger.info("{} has joined the group {}".format(data['username'], data['group']))
    join_room(data['group'])
    socketio.emit('join_group_announcement', data, room=data['group'])

@socketio.on('send_message')
def send_message_event(data):
    app.logger.info("{} has sent message to the room {}: {}".format(data['username'],
                                                                    data['group'],
                                                                    data['message']))
    data['created_at'] = datetime.now().strftime("%d %b, %H:%M")
    Message().save_message(data["group"], data['message'], data['username'], data['created_at'] )
    socketio.emit('receive_message', data, room=data['group'])



@login_manager.user_loader
def load_user(username):
    return Authorization().get_user(username)

if __name__=="__main__":
    socketio.run(app, debug =True)
