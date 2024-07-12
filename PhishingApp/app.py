from flask import Flask, request, redirect, render_template
import sqlite3

app = Flask(__name__)

DATABASE = 'phishing_simulation.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    return conn

@app.route('/')
def index():
    return render_template('home.html')

@app.route('/phish')
def phish():
    employee_id = request.args.get('id')
    
    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT email FROM emails WHERE id=?', (employee_id,))
    result = c.fetchone()
    
    if result:
        email = result[0]
        c.execute('INSERT INTO winners (email) VALUES (?)', (email,))
        conn.commit()
        conn.close()
        return redirect('/home')
    else:
        conn.close()
        return 'Incorrect employee ID'

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/aboutme')
def aboutme():
    return render_template('aboutme.html')

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  
    return conn

@app.route('/statistics')
def statistics():
    with get_db() as conn:
        c = conn.cursor()
        c.execute('SELECT COUNT(*) FROM emails')
        participants_count = c.fetchone()[0]
        c.execute('SELECT COUNT(*) FROM winners')
        winners_count = c.fetchone()[0]

    return render_template('statistics.html', participants_count=participants_count, winners_count=winners_count)
@app.route('/phishing')
def phishing():
    return render_template('phishing.html')

if __name__ == '__main__':
    app.run(debug=True)