import sqlite3 as sql
from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify # for returning json from requests
import bcrypt
from flask import Flask, session
from flask.sessions import SessionInterface
from beaker.middleware import SessionMiddleware

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

def insertUser(username,password):
    con = sql.connect("database.db")
    cur = con.cursor()
    cur.execute("INSERT INTO users (username,password) VALUES (?,?)", (username,password))
    con.commit()
    con.close()

def retrieveUsers():
    con = sql.connect("database.db")
    cur = con.cursor()
    cur.execute("SELECT username, password FROM users")
    users = cur.fetchall()
    con.close()
    return users

def findUser(username):
    con = sql.connect("database.db")
    cur = con.cursor()
    cur.execute("select username, password from users where username=?", (username,))
    user = cur.fetchone()
    con.close()
    return user
    #return {'username': user[0]

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    if 'username' not in request.form and 'password' not in request.form:
        return jsonify({'error':"incomplete-params"})
    username = request.form['username']
    password = request.form['password']

    user = findUser(username)
    db_pw = user[1].decode('utf-8')
    if user is None:
        return jsonify({'error':"bad-username"})
    
    if bcrypt.hashpw(password.encode('utf-8'), user[1]) == user[1]:
        session['loggedin'] = True
        return jsonify({'error':""})
    else:
        return jsonify({'error':"bad-login"})

@app.route('/register', methods=['POST'])
def register():
    if request.method=='POST':
       username = request.form['username']
       password = request.form['password']
       if findUser(username) is not None:
           return jsonify({'error':"username-taken"})
       insertUser(username, bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()))
       users = retrieveUsers()
       return jsonify({'error':""})
    else:
       return jsonify({'error':True, 'errmsg': "Register only accepts a POST."})

if __name__ == '__main__':
    app.wsgi_app = SessionMiddleware(app.wsgi_app, session_opts)
    app.session_interface = BeakerSessionInterface()
    app.run(debug=False, host='0.0.0.0')
