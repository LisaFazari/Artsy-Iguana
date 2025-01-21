from flask import Flask, make_response, render_template, request, redirect, url_for
from flask_login import UserMixin
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

# Database setup
def init_db():
    # Connecting to the sqlite3 database 
    conn = sqlite3.connect('artsy_iguana.db')
    c = conn.cursor()

    # Users table (both artists and consumers)
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  email TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  is_artist BOOLEAN NOT NULL,
                  bio TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Artwork table
    c.execute('''CREATE TABLE IF NOT EXISTS artwork
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  artist_id INTEGER NOT NULL,
                  title TEXT NOT NULL,
                  description TEXT,
                  price DECIMAL(10,2) NOT NULL,
                  image_path TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (artist_id) REFERENCES users (id))''')

    # Wishlist table
    # c.execute('''CREATE TABLE IF NOT EXISTS wishlist
    #              (id INTEGER PRIMARY KEY AUTOINCREMENT,
    #               user_id INTEGER NOT NULL,
    #               artwork_id INTEGER NOT NULL,
    #               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    #               FOREIGN KEY (user_id) REFERENCES users (id),
    #               FOREIGN KEY (artwork_id) REFERENCES artwork (id))''')

    conn.commit()
    conn.close()

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, is_artist):
        # User attributes 
        self.id = id
        self.username = username
        self.email = email
        self.is_artist = is_artist

# Flask-Login to load a user by their ID
def load_user(user_id):
    # Connecting to the sqlite3 database
    conn = sqlite3.connect('artsy_iguana.db')
    c = conn.cursor()
    # Query the database for the users data using their ID
    c.execute('SELECT id, username, email, is_artist FROM users WHERE id = ?', (user_id,))
    # Fetching the first matching row of data
    user_data = c.fetchone()
    conn.close()
    # If the user data is found, create and return the user
    if user_data:
        return User(*user_data)
    # Returning None if no user data is found
    return None

def get_user(email, password):
    # Connect to the SQLite database
    conn = sqlite3.connect('artsy_iguana.db')
    c = conn.cursor()

    # Query to fetch user details (id, username, is_artist)
    query = "SELECT id, username, email, is_artist FROM users WHERE email = ? AND password = ?"
    # Using the email and password query 
    c.execute(query, (email, password))  
    # Fetching the first matching user
    user = c.fetchone()  
    conn.close()
    
    if user:
        return User(*user)
    return None 

# Routes
@app.route('/')
# Route for home.html
@app.route('/home')
def home():
    # Connecting to the sqlite3 database
    conn = sqlite3.connect('artsy_iguana.db')
    c = conn.cursor()

    # Fetch the last 3 artwork pieces along with the username, ordered by ID (or timestamp) descending
    c.execute('''
        SELECT artwork.id, artwork.title, artwork.image_path, users.username, artwork.artist_id
        FROM artwork
        JOIN users ON artwork.artist_id = users.id
        ORDER BY artwork.id DESC 
        LIMIT 3
    ''')
    # Fetching the query of data from the result
    artworks = c.fetchall()  

    conn.close()

    # Pass the artwork data to the template
    return render_template('home.html', artworks=artworks)

# Route for login.html
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Requesting the log in credentials
        password = request.form['password']
        email = request.form['email']

        # Validate the user and get the username
        user = get_user(email, password)

        if user:
            # Extracting the user details
            user_id = user.id
            username = user.username
            is_artist = user.is_artist

            # Set cookies with the user's info
            response = make_response(redirect(request.args.get('next') or url_for('home')))
            response.set_cookie('user_id', str(user_id))
            response.set_cookie('username', username)
            response.set_cookie('is_artist', str(is_artist))
            
            return response
        else:
            # Handle invalid login
            return redirect(url_for('login', error="invalid"))
            
    else:
        # If wrong credentials used, alert with error message
        error_message = request.args.get('error', None)
        return render_template('login.html', error=error_message)
            
# Route for signup.html
@app.route('/register', methods=['GET', 'POST'])
def register():
    # Checking if the request is a POST = form submission
    if request.method == 'POST':
        # Retrieving the data filled in the form by the user 
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        # Checking if the accountype field in the form is filled in as 'Artist'
        is_artist = request.form['accountType']

        # Connecting to the sqlite3 database
        conn = sqlite3.connect('artsy_iguana.db')
        c = conn.cursor()

        try:
            # Inserting the new user data into the 'users' table
            c.execute('INSERT INTO users (username, email, password, is_artist) VALUES (?, ?, ?, ?)',
                     (username, email, password, is_artist))
            conn.commit()
            return redirect(url_for('login', message='Registration successful! Please login.', status='success'))
        except sqlite3.IntegrityError:
            # Redirect with an error message
            return redirect(url_for('register', message='Username or email already exists.', status='error'))
        finally:
            conn.close()

    return render_template('signup.html')

# Route for signout
@app.route('/signout', methods=['POST'])
def signout():
    response = make_response(redirect(url_for('home')))
    # Clearing the user_id, username and is_artist cookie by setting their value to empty and expiring them to 0
    response.set_cookie('user_id', '', expires=0)
    response.set_cookie('username', '', expires=0)
    response.set_cookie('is_artist', '', expires=0)

    # Successfully logging out to user and redirecting them to the home page
    return response

# Route for myprofile.html
@app.route('/myprofile')
def myprofile():
    # Get user data from cookies
    user_id = request.cookies.get('user_id')
    username = request.cookies.get('username')

    # Checking if user is not an artist
    if user_id is None or username is None:  # Checking if user is not an artist
        return redirect(url_for('myprofile'))
    else:
        # Connecting to the sqlite3 database
        conn = sqlite3.connect('artsy_iguana.db')
        c = conn.cursor()

        # Fetch the last 3 artwork pieces along with the username, ordered by ID (or timestamp) descending
        c.execute(f'''
            SELECT artwork.id, artwork.title, artwork.image_path, users.username, artwork.artist_id
            FROM artwork
            JOIN users ON artwork.artist_id = users.id
            WHERE artwork.artist_id = {user_id}
            ORDER BY artwork.id DESC
        ''')
        # Fetching the query of data from the result
        artworks = c.fetchall()  
        conn.close()

        # Pass the artwork data to the template
        return render_template('myprofile.html', artworks=artworks)

# Route for gallery.html
@app.route('/gallery')
def gallery():
    # Connecting to the sqlite3 database
    conn = sqlite3.connect('artsy_iguana.db')
    c = conn.cursor()
    
    # Fetching all the submitted artwork along with the username to be displayed on the gallery page
    c.execute('''
        SELECT artwork.id, artwork.title, artwork.image_path, users.username, artwork.artist_id
        FROM artwork
        JOIN users ON artwork.artist_id = users.id
        ORDER BY artwork.id DESC 
    ''')
    artworks = c.fetchall()
    conn.close()
    
    return render_template('gallery.html', artworks=artworks)

# Route for the UPLOAD_FOLDER with the uploaded artwork from registered artists
@app.route('/upload_artwork', methods=['GET', 'POST'])
def upload_artwork():
    # Get user data from cookies
    user_id = request.cookies.get('user_id')
    username = request.cookies.get('username')
    is_artist = request.cookies.get('is_artist')

    # Checking if user is not an artist
    if user_id is None or username is None or is_artist != '1':  
        return redirect(url_for('myprofile'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        price = request.form['price']
        image = request.files['image']

        if image:
            # Save image with a unique name based on the current timestamp
            filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{image.filename}"
            # Define the path for the user's artwork folder
            user_folder = os.path.join('./static/UPLOAD_FOLDER', str(user_id))

            # Create the directory if it doesn't exist
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)

            # Save the image to the user's folder
            image.save(os.path.join(user_folder, filename))

            # Insert artwork data into the database
            conn = sqlite3.connect('artsy_iguana.db')
            c = conn.cursor()
            c.execute('INSERT INTO artwork (artist_id, title, description, price, image_path) VALUES (?, ?, ?, ?, ?)',
                     (user_id, title, description, price, filename))
            conn.commit()
            conn.close()

            return render_template('myprofile.html')
        
    return render_template('myprofile.html')

# Route for search function
@app.route('/search', methods=['GET'])
def search():
    # Retrieving the search query from the user and converting it to lowercase
    query = request.args.get('query', '').lower()
    # Connecting to the sqlite3 database
    conn = sqlite3.connect('artsy_iguana.db')
    c = conn.cursor()

    # Searching for a match from the search query to the database, searching for either the users.username or artwork.title
    c.execute("""
        SELECT artwork.id, artwork.title, artwork.image_path, users.username, artwork.artist_id
        FROM users
        INNER JOIN artwork ON users.id = artwork.artist_id
        WHERE LOWER(users.username) LIKE ? OR LOWER(artwork.title) LIKE ?
    """, (f'%{query}%', f'%{query}%'))

    # Fetching all the matching data from the query
    results = c.fetchall()
    conn.close()

    return render_template('gallery.html', artworks=results)

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
