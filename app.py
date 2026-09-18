from flask import Flask, render_template, request, redirect
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()  # <-- moved here, runs every time the app starts (both locally and on Render)

@app.route('/')
def home():
    search = request.args.get('search', '')
    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    if search:
        cursor.execute('SELECT * FROM contacts WHERE name LIKE ? ORDER BY name', ('%' + search + '%',))
    else:
        cursor.execute('SELECT * FROM contacts ORDER BY name')
    contacts = cursor.fetchall()
    conn.close()
    return render_template('index.html', contacts=contacts, search=search)

@app.route('/add', methods=['POST'])
def add_contact():
    name = request.form['name'].strip()
    phone = request.form['phone'].strip()
    email = request.form['email'].strip()

    if not name:
        return redirect('/')

    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO contacts (name, phone, email) VALUES (?, ?, ?)', (name, phone, email))
    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/edit/<int:contact_id>')
def edit_contact(contact_id):
    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts WHERE id = ?', (contact_id,))
    contact = cursor.fetchone()
    conn.close()
    return render_template('edit.html', contact=contact)

@app.route('/update/<int:contact_id>', methods=['POST'])
def update_contact(contact_id):
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']

    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE contacts SET name = ?, phone = ?, email = ? WHERE id = ?',
                   (name, phone, email, contact_id))
    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/delete/<int:contact_id>')
def delete_contact(contact_id):
    conn = sqlite3.connect('contacts.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM contacts WHERE id = ?', (contact_id,))
    conn.commit()
    conn.close()

    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)