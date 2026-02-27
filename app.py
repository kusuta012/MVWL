from flask import Flask, render_template, redirect, request, session, flash, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user # type: ignore
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import sqlite3
import requests
import random
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


OMDB_API_KEY = os.getenv("OMDB_API_KEY")


def init_db():
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS movies
              (id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              title TEXT NOT NULL,
              year TEXT,
              poster TEXT,
              rating TEXT,
              watched BOOLEAN DEFAULT 0,
              FOREIGN KEY (user_id) REFERENCES users (id))''')

    conn.commit()
    conn.close()


class User(UserMixin):
    def __init__(self, id, username):
        self.id = id  
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()
    
    if user:
        return User(user[0], user[1])
    return None

@app.route('/')
def land():
    return render_template('land.html')

    
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        hashed_password = generate_password_hash(password)
        
        try: 
            conn = sqlite3.connect('movies.db')
            c = conn.cursor()
            c.execute('INSERT INTO users (username, password) VALUES (?,?)', (username, hashed_password))
            conn.commit()
            conn.close()
            
            flash('Account created', 'success')
        except sqlite3.IntegrityError:
            flash('Username already exists', 'error')
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('movies.db')
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        conn.close()
        
        if user and check_password_hash(user[2], password):
            user_obj = User(user[0], user[1])
            login_user(user_obj)
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', message=['Invalid username or password'])

    return render_template('login.html')
        
if __name__== '__main__':
    init_db()
    app.run(debug=True)