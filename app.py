from flask import Flask, render_template, redirect, request, flash, url_for
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user # type: ignore
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash 
import sqlite3
import requests
import random
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "30 per hour"],
    storage_uri="memory://"
)

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
@limiter.limit("5 per hour")
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
@limiter.limit("10 per hour")
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute('SELECT * FROM movies WHERE user_id = ?', (current_user.id,))
    movies = c.fetchall()
    conn.close()
    
    return render_template('dashboard.html', movies=movies)

@app.route('/add_movie', methods=['GET', 'POST'])
@limiter.limit("25 per hour")
@login_required
def add_movie():
    if request.method == 'POST':
        movie_title = request.form['title']
        
        print(f'{OMDB_API_KEY}')
        print(f'{movie_title}')
        
        url = f'http://www.omdbapi.com/?t={movie_title}&apikey={OMDB_API_KEY}'
        print(f'{url}')
        response = requests.get(url)
        data = response.json()
        
        print(f"Response: {data}")
        
        if data.get('Response') == 'True':
            title = data.get('Title')
            year = data.get('Year')
            poster = data.get('Poster')
            rating = data.get('imdbRating')
            
            conn = sqlite3.connect('movies.db')
            c = conn.cursor()
            c.execute('INSERT INTO movies (user_id, title, year, poster, rating) VALUES (?, ?, ?, ?, ?)', (current_user.id, title, year, poster, rating))
            conn.commit()
            conn.close()
            
            flash(f'{title} added to watchlist!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash(f'Movie not found, Try again', 'error')
    
    return render_template('add_movie.html')

@app.route('/del_movie/<int:movie_id>')
@login_required
def del_movie(movie_id):
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute('DELETE FROM movies WHERE id = ? AND user_id = ?', (movie_id, current_user.id))
    conn.commit()
    conn.close()
    flash('Movie deleted', 'success')
    return redirect(url_for('dashboard'))

@app.route('/mark_watched/<int:movie_id>')
@login_required
def mark_watched(movie_id):
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute('UPDATE movies SET watched = 1 WHERE id = ? AND user_id = ?', (movie_id, current_user.id))
    conn.commit()
    conn.close()
    flash('Marked as watched', 'success')
    return redirect(url_for('dashboard'))

@app.route('/random_pick')
@login_required
def random_pick():
    conn = sqlite3.connect('movies.db')
    c = conn.cursor()
    c.execute('SELECT * FROM movies WHERE user_id = ? AND watched = 0', (current_user.id,))
    movies = c.fetchall()
    conn.close()
    
    if movies:
        pick = random.choice(movies)
        flash(f"Tonight's pick: {pick[2]} ({pick[3]})", 'success')  
    else:
        flash('No unwanted movies!', 'error')
    
    return redirect(url_for('dashboard'))
    
    
@app.errorhandler(429)
def ratelimite(e):
    flash('Too many reuqests, Please try again later', 'error')
    return redirect(url_for('dashboard')), 429
    
    
            
if __name__== '__main__':
    init_db()
    app.run(debug=False, host='0.0.0.0', port=6767)