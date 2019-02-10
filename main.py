import sqlite3 as sql
from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify # for returning json from requests
import bcrypt
from flask import Flask, session
from flask.sessions import SessionInterface
from beaker.middleware import SessionMiddleware
from db import get_db, init_app

session_opts = {
    'session.type': 'memory',
    'session.auto': True,
    'session.secret': "test-secret"
}

class BeakerSessionInterface(SessionInterface):
    def open_session(self, app, request):
        session = request.environ['beaker.session']
        return session

    def save_session(self, app, session, response):
        session.save()

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY='dev',
    DATABASE='database.db',
)
init_app(app) # initialize the database to this app

def insertUser(username,password,email,realname,parentid):
    mdb = get_db()
    mdb.execute("INSERT INTO users (username, password, email, realname, parentid) VALUES (?,?,?,?,?)", (username,password,email,realname,parentid))
    mdb.commit()

def findUser(**kwargs):
    mdb = get_db()
    if 'username' in kwargs:
        user = mdb.execute("select id, username, password, parentid, realname from users where username=?", (kwargs['username'],)).fetchone()
    elif 'id' in kwargs:
        user = mdb.execute("select id, username, password, parentid, realname from users where id=?", (kwargs['id'],)).fetchone()
    else:
        return None
    if user is None:
        return None
    return {"id":int(user[0]), "username":user[1], "password":user[2], "parent":int(user[3]), "realname":user[4]}

def check_params(r, *args):
    for param in args:
        if param not in r:
            return False
    return True

def logged_in():
    if 'loggedin' not in session or not session['loggedin']:
        return False
    return True

@app.route('/login', methods=['POST'])
def login():
    if not check_params(request.form, 'username', 'password'):
        return jsonify({'error':"incomplete-params"})
    username = request.form['username']
    password = request.form['password']
    
    user = findUser(username=username)
    if user is None:
        return jsonify({'error':"bad-username"})
    
    if bcrypt.hashpw(password.encode('utf-8'), user['password']) == user['password']:
        session['loggedin'] = True
        session['userid'] = user['id']
        return jsonify({'error':"", 'userid':user['id']})
    else:
        return jsonify({'error':"bad-login"})

@app.route('/register', methods=['POST'])
def register():
    if not check_params(request.form, 'username', 'password', 'email', 'realname', 'parentid'):
       username = request.form['username']
       password = request.form['password']
       email = request.form['email']
       realname = request.form['realname']
       parentid = 0
       # if we're creating an account but we're already logged in,
       # then treat the account we're making as a child account
       # (so the parent is the current user)
       if logged_in():
           parentid = session['userid']
       
       if findUser(username=username) is not None:
           return jsonify({'error':"username-taken"})
       insertUser(username, bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()), email, realname, parentid)
       return jsonify({'error':""})
    else:
       return jsonify({'error':True, 'errmsg': "Register only accepts a POST."})

if __name__ == '__main__':
    app.wsgi_app = SessionMiddleware(app.wsgi_app, session_opts)
    app.session_interface = BeakerSessionInterface()
    app.run(debug=False, host='0.0.0.0')
