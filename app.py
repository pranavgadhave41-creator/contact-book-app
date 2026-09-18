from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-this')

DATABASE_URL = os.environ.get('DATABASE_URL')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            user_id INTEGER REFERENCES users(id)
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

init_db()

class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

@login_manager.user_loader
def load_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username FROM users WHERE id = %s', (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return User(row[0], row[1])
    return None

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        if not username or not password:
            flash('Username and password are required.')
            return redirect('/signup')

        hashed = generate_password_hash(password)

        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed))
            conn.commit()
        except psycopg2.errors.UniqueViolation:
            conn.rollback()
            flash('Username already taken.')
            cursor.close()
            conn.close()
            return redirect('/signup')
        cursor.close()
        conn.close()

        return redirect('/login')

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, password FROM users WHERE username = %s', (username,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if row and check_password_hash(row[2], password):
            user = User(row[0], row[1])
            login_user(user)
            return redirect('/')
        else:
            flash('Invalid username or password.')
            return redirect('/login')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/login')

@app.route('/')
@login_required
def home():
    search = request.args.get('search', '')
    conn = get_connection()
    cursor = conn.cursor()
    if search:
        cursor.execute('SELECT * FROM contacts WHERE user_id = %s AND name LIKE %s ORDER BY name',
                       (current_user.id, '%' + search + '%'))
    else:
        cursor.execute('SELECT * FROM contacts WHERE user_id = %s ORDER BY name', (current_user.id,))
    contacts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', contacts=contacts, search=search)

@app.route('/add', methods=['POST'])
@login_required
def add_contact():
    name = request.form['name'].strip()
    phone = request.form['phone'].strip()
    email = request.form['email'].strip()

    if not name:
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO contacts (name, phone, email, user_id) VALUES (%s, %s, %s, %s)',
                   (name, phone, email, current_user.id))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/')

@app.route('/edit/<int:contact_id>')
@login_required
def edit_contact(contact_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts WHERE id = %s AND user_id = %s', (contact_id, current_user.id))
    contact = cursor.fetchone()
    cursor.close()
    conn.close()
    if not contact:
        return redirect('/')
    return render_template('edit.html', contact=contact)

@app.route('/update/<int:contact_id>', methods=['POST'])
@login_required
def update_contact(contact_id):
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE contacts SET name = %s, phone = %s, email = %s WHERE id = %s AND user_id = %s',
                   (name, phone, email, contact_id, current_user.id))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/')

@app.route('/delete/<int:contact_id>')
@login_required
def delete_contact(contact_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM contacts WHERE id = %s AND user_id = %s', (contact_id, current_user.id))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)