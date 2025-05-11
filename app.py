# Final Project
import sqlite3
from functools import wraps
from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, g
)
import urllib.request
import json
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'franklyn-secret-key'

# Database setup
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect('books.db')
        g.db.row_factory = sqlite3.Row
    return g.db

# close the database connection after the request is processed
@app.teardown_appcontext 
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()


# I created this login_required to prevent users from accessing the dashboard without logging in.
# This has its own function so that it can be used in other routes to avoid code repetition.
# wraps is used to preserve the original function's meta data
# *args and **kwargs are used to pass any additional arguments to the function
# *args allows the function to accept any number of positional arguments
# **kwargs allows the function to accept any number of keyword arguments
# Together they make the decorator flexible and able to handle any function 

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Error: You must be logged in to access this page')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', 
                         (username, password)).fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'{username} has logged in successfully')
            return redirect(url_for('dashboard'))
        flash('Incorrect username or password, please try again.')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        
        # Check if username exists
        if db.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone():
            flash(f'Username: {username} already exists')
            return redirect(url_for('register'))
        
        # Create new user
        db.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                  (username, password))
        db.commit()
        flash('Welcome to the app, Registration is successful. Please login.')
        return redirect(url_for('login'))
    return render_template('register.html')

# Note there is @login_required repeated below to prevent users 
# to ensure all routes are protected from unauthenticated # users.

@app.route('/dashboard')
@login_required
def dashboard():
    db = get_db()
    books = db.execute('''
        SELECT * FROM books 
        WHERE user_id = ? 
        ORDER BY date_added DESC
    ''', (session['user_id'],)).fetchall()
    return render_template('dashboard.html', books=books)

@app.route('/search_book', methods=['POST'])
@login_required
def search_book():
    isbn = request.form.get('isbn')
    if not isbn:
        flash('Please enter the book ISBN number to search for')
        return redirect(url_for('dashboard'))
    
    try:
        # To use the google book api you need to do the following:
        # 1. Createa dynamic API URL that takes in the ISBN query parameter
        # 2. Open the URL using urllib.request.urlopen()
        # 3. Read the response 
        # 4. Decode the response to string
        # 5. Parse JSON response into a Python dictionary
        # The good news is that the google book api is free to use and does not require an api key, it is public.
        
        url = f'https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}'
        print(f"Searching for ISBN: {isbn}")  
        
        with urllib.request.urlopen(url) as response:
            response_data = response.read().decode('utf-8')
            data = json.loads(response_data)
            # print(f"API Response: {data}")  
        
        if 'items' not in data:
            flash(f'Book with ISBN {isbn} not found in the Google Books database. Please verify the ISBN number.')
            return redirect(url_for('dashboard'))
        
        book_data = data['items'][0]['volumeInfo']
        # print(f"Book data: {book_data}")  
        
        db = get_db()
        
        # Check if book already exists for user
        existing = db.execute('''
            SELECT id FROM books 
            WHERE isbn = ? AND user_id = ?
        ''', (isbn, session['user_id'])).fetchone()
        
        if existing:
            flash('This book already exists in your collection, you cannot add it again')
            return redirect(url_for('dashboard'))
        
        # Add new book with formatted date
        current_date = datetime.now().strftime('%Y-%m-%d')
        db.execute('''
            INSERT INTO books (isbn, title, author, page_count, rating, published_date, category, thumbnail_url, user_id, date_added)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            isbn,
            book_data.get('title', 'Unknown Title'),
            ', '.join(book_data.get('authors', ['Unknown Author'])),
            book_data.get('pageCount', 0),
            book_data.get('averageRating', 0.0),
            book_data.get('publishedDate', 'Unknown'),
            ', '.join(book_data.get('categories', ['Uncategorized'])),
            book_data.get('imageLinks', {}).get('thumbnail', ''),
            session['user_id'],
            current_date
        ))
        db.commit()
        flash(f'Book "{book_data.get("title", "Unknown Title")}" added successfully!')
    except Exception as e:
        flash(f'Error: {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/delete_book/<int:book_id>', methods=['POST'])
@login_required
def delete_book(book_id):
    db = get_db()
    # This is used to check if the book belongs to a specific user
    book = db.execute('''
        SELECT id FROM books 
        WHERE id = ? AND user_id = ?
    ''', (book_id, session['user_id'])).fetchone()
    # Redirect back to the dashboard if the book does not belong to the user
    if not book:
        flash('You dont have permission to delete this book')
        return redirect(url_for('dashboard'))
    # Delete the book from the database
    db.execute('DELETE FROM books WHERE id = ?', (book_id,))
    db.commit() # Save deletion to the database
    flash('Book has been deleted from the database')
    return redirect(url_for('dashboard'))

@app.route('/logout')
@login_required
def logout():
    session.clear() # Clear the session
    flash('User has been logged out successfully')
    return redirect(url_for('index'))

if __name__ == '__main__':
    with app.app_context():
        db = get_db()
        # Create users table to hold the users of the application
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')
        # Create books table to hold the books added by the user
        db.execute('''
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                isbn TEXT NOT NULL,
                title TEXT NOT NULL,
                author TEXT,
                page_count INTEGER,
                rating REAL,
                published_date TEXT,
                category TEXT,
                thumbnail_url TEXT,
                user_id INTEGER NOT NULL,
                date_added TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        db.commit()
    app.run(debug=True) 