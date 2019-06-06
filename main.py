import sqlite3 as sql
from flask import Flask
from flask import render_template
from flask import request
from flask import jsonify # for returning json from requests
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, session
from flask.sessions import SessionInterface
from beaker.middleware import SessionMiddleware
from db import get_db, init_app
from datetime import date
from pathlib import Path


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

def insertUser(username,password,email,realname,parentid,born,gender):
    mdb = get_db()
    #print("value ", date.today().year - int(age), " and ", int(age))
    mdb.execute("INSERT INTO users (username, password, email, realname, parentid, born, gender, credits) VALUES (?,?,?,?,?,?,?,?)", (username,password,email,realname,parentid,born, gender, 0))
    mdb.commit()

def findUser(**kwargs):
    mdb = get_db()
    if 'username' in kwargs:
        user = mdb.execute("select id, username, password, parentid, realname, email, born, credits from users where username=?", (kwargs['username'],)).fetchone()
    elif 'id' in kwargs:
        user = mdb.execute("select id, username, password, parentid, realname, email, born, credits from users where id=?", (kwargs['id'],)).fetchone()
    else:
        return None
    if user is None:
        return None
    colle = findUserCollections(int(user[0]))
    
    return {"id":int(user[0]), "username":user[1], "password":user[2], "parent":int(user[3]), "realname":user[4], "email":user[5], "born":user[6], "collections":colle, "credits":int(user[7])}

def getCredits(id):
    u = findUser(id=id)
    return u['credits']

def updateCredits(id, n):
    mdb = get_db()
    mdb.execute("update users set credits=? where id=?", (getCredits(id)+n, id))
    mdb.commit()

def updateUser(id, username, password, realname, email, born):
    mdb = get_db()
    pw = generate_password_hash(password)
    print("username: ", username)
    mdb.execute("update users set username=?, password=?, realname=?, email=?, born=? where id=?", (username, pw, realname, email, born, id))
    mdb.commit()

def findChildren(uid):
    mdb = get_db()
    
    # get the IDs of this user's children
    children = mdb.execute("select id from users where parentid=?", (uid,)).fetchall()
    if children is None:
        return None
    ret = []

    # look up each child in the database and return data about them
    for child in children:
        c_userdata = findUser(id=child[0])
        if c_userdata is None:
            return ret
        ret.append(c_userdata)
    return ret

def hasChild(uid, cid):
    mdb = get_db()

    child = mdb.execute("select id from users where id=? and parentid=?", (cid, uid)).fetchone()

    if child is None:
        return False
    return True

def findUserCollections(uid):
    #print(session)
    mdb = get_db()
    collections = mdb.execute("select collections.id, title, xmldata from collection_owners inner join collections on collection_owners.cid = collections.id where uid=?", (uid,)).fetchall()
    if collections is not None:
        ret = []
        for coll in collections:
            xml_file = Path(coll[2])
            if xml_file.is_file():
                with open(xml_file, 'r') as f:
                    ret.append({"cid":int(coll[0]), "title":coll[1], "xmldata":f.read()})
        return ret
    return None

def findUserChildCollections(uid):
    pass

def check_params(r, *args):
    for param in args:
        if param not in r:
            return False
    return True

def logged_in():
    if 'loggedin' not in session or not session['loggedin']:
        return False
    return True

@app.route('/loginform', methods=['GET'])
def loginform():
    return "<form method='POST' action='/login'><input type='text' name='username'><input type='password' name='password'><input type='submit'></form>"

@app.route('/login', methods=['POST'])
def login():
    if not check_params(request.form, 'username', 'password'):
        return jsonify({'error':"incomplete-params"})
    username = request.form['username']
    password = request.form['password']
    
    user = findUser(username=username)
    if user is None:
        return jsonify({'error':"bad-username"})

    print(user['password'])
    print(password)
    if check_password_hash(user['password'], password):
        session['loggedin'] = True
        session['userid'] = user['id']
        return jsonify({'error':"", 'userid':user['id']})
    else:
        return jsonify({'error':"bad-login"})


@app.route('/profile', methods=['GET'])
def profile():
    pass

@app.route('/my_collections', methods=['GET'])
def my_collections():
    print(session)
    if not logged_in():
        return jsonify({'error':"restricted-login"})
    cs = findUserCollections(session['userid'])
    if cs is None:
        return jsonify({'error':"", 'collections':[]})
    return jsonify({'error':"", 'collections':cs})

@app.route('/register', methods=['POST'])
def register():
    if check_params(request.form, 'username', 'password', 'email', 'realname', 'parentid', 'born', 'gender'):
       username = request.form['username']
       password = request.form['password']
       email = request.form['email']
       realname = request.form['realname']
       born = request.form['born']
       gender = request.form['gender']
       parentid = int(request.form['parentid'])
       # if we're creating an account but we're already logged in,
       # then treat the account we're making as a child account
       # (so the parent is the current user)
       #if logged_in():
       #    parentid = session['userid']
       
       if findUser(username=username) is not None:
           return jsonify({'error':"username-taken"})
       insertUser(username, generate_password_hash(request.form['password']), email, realname, parentid, born, gender)
       return jsonify({'error':""})
    else:
       return jsonify({'error':"incomplete-params"})

@app.route("/myinfo", methods=["POST"])
def my_info():
    if not logged_in():
        return jsonify({'error':'unauthorised'})
    else:
        me =  findUser(id=session["userid"])
        return jsonify({"user":me, "children": findChildren(session["userid"]), "error":""})

@app.route("/updateinfo", methods=["POST"])
def update_info():
    if not logged_in():
        return jsonify({'error':'unauthorized'})
    me = findUser(id=session['userid'])
    if me is not None:
        if not check_params(request.form, 'username', 'password', 'realname', 'email', 'born'):
            return jsonify({'error':"incomplete-params"})
        updateUser(session['userid'], request.form['username'], request.form['password'], request.form['realname'], request.form['email'], request.form['born'])
        return jsonify({'error':""})
    return jsonify({'error':'bad-session'})

@app.route('/updatecredits', methods=['POST'])
def update_credits():
    if not logged_in():
        return jsonify({'error':'unauthorized'})
    me = findUser(id=session['userid'])
    if me is not None:
        if not check_params(request.form, 'ncredits'):
            return jsonify({'error':"incomplete-params"})
        try:
            ncredits = int(request.form['ncredits'])
            updateCredits(session['userid'], ncredits)
            return jsonify({'error':"", 'credits':ncredits})
        except ValueError:
            return jsonify({'error':'incomplete-params'})

@app.route("/updatestudentinfo", methods=["POST"])
def update_student_info():
    if not logged_in():
        return jsonify({'error':'unauthorized'})
    me = findUser(id=session['userid'])
    if me is not None:
        if not check_params(request.form, 'username', 'password', 'realname', 'email', 'born', 'studentid'):
            return jsonify({'error':"incomplete-params"})
        try:
             if not hasChild(session['userid'], int(request.form['studentid'])):
                 return jsonify({'error':"not-your-child"})
             updateUser(int(request.form['studentid']), request.form['username'],
                        request.form['password'], request.form['realname'], request.form['email'], request.form['born'])
        except ValueError:
            return jsonify({'error':"incomplete-params"})
        return jsonify({'error':""})
    return jsonify({'error':'bad-session'})

if __name__ == '__main__':
    app.wsgi_app = SessionMiddleware(app.wsgi_app, session_opts)
    app.session_interface = BeakerSessionInterface()
    app.run(debug=True, host='0.0.0.0')#, ssl_context='adhoc')

