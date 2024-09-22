from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import random
import string
from datetime import datetime

app = Flask(__name__)

# Create SQLite database if it doesn't exist
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS bids (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            bid_amount REAL NOT NULL,
            bid_id TEXT NOT NULL UNIQUE,
            bid_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Function to generate a unique 6-digit Bid ID
def generate_bid_id():
    return ''.join(random.choices(string.digits, k=6))

# Function to redact alternate letters of a name
def redact_name(name):
    return ''.join([char if i % 2 == 0 else '*' for i, char in enumerate(name)])

# Route to display the form and countdown
@app.route('/')
def index():
    return render_template('index.html')

# Route to handle form submission
@app.route('/submit_bid', methods=['POST'])
def submit_bid():
    name = request.form['name']
    phone = request.form['phone']
    email = request.form['email']
    bid_amount = request.form['bid_amount']

    # Input validation
    if not name or not phone or not email or not bid_amount:
        return "All fields are required."

    try:
        bid_amount = float(bid_amount)
    except ValueError:
        return "Invalid bid amount."

    if bid_amount < 20000:
        return "Minimum bid amount is ₹20,000."

    bid_id = generate_bid_id()
    bid_time = datetime.now()

    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('INSERT INTO bids (name, phone, email, bid_amount, bid_id, bid_time) VALUES (?, ?, ?, ?, ?, ?)', 
                  (name, phone, email, bid_amount, bid_id, bid_time))
        conn.commit()
    except Exception as e:
        return f"An error occurred: {str(e)}"
    finally:
        conn.close()

    return redirect(url_for('submit_bid_success', bid_amount=bid_amount, name=name, bid_id=bid_id))

@app.route('/submit_bid')
def submit_bid_success():
    bid_amount = request.args.get('bid_amount')
    name = request.args.get('name')
    bid_id = request.args.get('bid_id')
    return render_template('submit_bid.html', bid_amount=bid_amount, name=name, bid_id=bid_id)

@app.route('/highest_bid')
def highest_bid():
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute('SELECT name, bid_amount, bid_id FROM bids ORDER BY bid_amount DESC LIMIT 1')
        result = c.fetchone()
    except Exception as e:
        return f"An error occurred while accessing the database: {str(e)}"
    finally:
        conn.close()

    if result:
        name, bid_amount, bid_id = result
        redacted_name = redact_name(name)
        return render_template('highest_bid.html', bid_amount=bid_amount, redacted_name=redacted_name, bid_id=bid_id)
    else:
        return render_template('highest_bid.html', bid_amount=0, redacted_name="No bids", bid_id="N/A")

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
