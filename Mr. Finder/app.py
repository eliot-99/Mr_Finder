# Import necessary modules
from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os

# Create Flask app
app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Database configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')

# Function to get a database connection
def get_connection():
    return sqlite3.connect(DATABASE_PATH)

# Initialize database tables
with app.app_context():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            enrollment TEXT NOT NULL UNIQUE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lost_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT NOT NULL,
            stream TEXT NOT NULL,
            year TEXT NOT NULL,
            contact TEXT NOT NULL,
            item_name TEXT NOT NULL,
            found_date TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()

# Define routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/choice/<int:user_id>')
def choice(user_id):
    return render_template('choice.html', user_id=user_id)

@app.route('/validate_user', methods=['POST'])
def validate_user():
    name = request.form.get('name')
    enrollment = request.form.get('enrollment')

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE name=? AND enrollment=?', (name, enrollment))
        user = cursor.fetchone()

    if user:
        return redirect(url_for('choice', user_id=user[0]))
    else:
        return render_template('invalid_user_register.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        enrollment = request.form.get('enrollment')

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE name=? AND enrollment=?', (name, enrollment))
            user = cursor.fetchone()

        if user:
            return render_template('invalid_user_register.html')

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (name, enrollment) VALUES (?, ?)', (name, enrollment))
            conn.commit()

        return render_template('registration_success.html', name=name)
    else:
        return render_template('register.html')

@app.route('/entry_form/<int:user_id>', methods=['GET', 'POST'])
def entry_form(user_id):
    if request.method == 'POST':
        name = request.form.get('name')
        stream = request.form.get('stream')
        year = request.form.get('year')
        contact = request.form.get('contact_no')
        item_name = request.form.get('item_name')
        found_date = request.form.get('date')

        # Check if any required field is empty
        if not all([name, stream, year, contact, item_name, found_date]):
            return render_template('entry_form.html', user_id=user_id, error="All fields are required")

        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO lost_items (user_id, name, stream, year, contact, item_name, found_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, stream, year, contact, item_name, found_date))
            conn.commit()

        return render_template('thank_you.html', user_id=user_id)

    return render_template('entry_form.html', user_id=user_id)

@app.route('/find/<int:user_id>', methods=['GET', 'POST'])
def find(user_id):
    if request.method == 'POST':
        item_name = request.form.get('item_name')

        with get_connection() as conn:
            cursor = conn.cursor()

            if item_name:
                cursor.execute('''
                    SELECT * FROM lost_items
                    WHERE user_id=? AND item_name=?
                ''', (user_id, item_name))
                results = cursor.fetchall()
                
                if results:
                    return render_template('results.html', user_id=user_id, search_results=results)
                else:
                    # If no matching name found, show all lost items
                    cursor.execute('''
                        SELECT * FROM lost_items
                        WHERE user_id=?
                    ''', (user_id,))
                    all_results = cursor.fetchall()
                    return render_template('results.html', user_id=user_id, search_results=all_results, error="No matching name found.")
            else:
                return render_template('find.html', user_id=user_id, error="Please provide item name.")

    return render_template('find.html', user_id=user_id)

if __name__ == '__main__':
    app.run(debug=True)
