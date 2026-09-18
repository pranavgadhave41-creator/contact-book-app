from flask import Flask, render_template, request, redirect
import psycopg2
import os

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL')

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

init_db()

@app.route('/')
def home():
    search = request.args.get('search', '')
    conn = get_connection()
    cursor = conn.cursor()
    if search:
        cursor.execute('SELECT * FROM contacts WHERE name LIKE %s ORDER BY name', ('%' + search + '%',))
    else:
        cursor.execute('SELECT * FROM contacts ORDER BY name')
    contacts = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', contacts=contacts, search=search)

@app.route('/add', methods=['POST'])
def add_contact():
    name = request.form['name'].strip()
    phone = request.form['phone'].strip()
    email = request.form['email'].strip()

    if not name:
        return redirect('/')

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO contacts (name, phone, email) VALUES (%s, %s, %s)', (name, phone, email))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/')

@app.route('/edit/<int:contact_id>')
def edit_contact(contact_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts WHERE id = %s', (contact_id,))
    contact = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('edit.html', contact=contact)

@app.route('/update/<int:contact_id>', methods=['POST'])
def update_contact(contact_id):
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE contacts SET name = %s, phone = %s, email = %s WHERE id = %s',
                   (name, phone, email, contact_id))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/')

@app.route('/delete/<int:contact_id>')
def delete_contact(contact_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM contacts WHERE id = %s', (contact_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)