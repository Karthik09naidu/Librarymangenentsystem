from flask import Flask, render_template, request, redirect, session, flash
from flask import Flask, render_template, request, redirect, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# Initialize Flask app
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'library'
mysql = MySQL(app)

# Routes
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        if user and check_password_hash(user[3], password):
            session['user_id'] = user[0]
            session['role'] = user[4]
            if user[4] == 'admin':
                return redirect('/admin_dashboard')
            return redirect('/user_dashboard')
        flash('Invalid credentials!')
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        role = request.form['role']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                    (name, email, password, role))
        mysql.connection.commit()
        cur.close()
        flash('Account created successfully!')
        return redirect('/login')
    return render_template('signup.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user_id' not in session or session['role'] != 'admin':
        return redirect('/login')
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books")
    books = cur.fetchall()
    cur.close()
    return render_template('admin_dashboard.html', books=books)

@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session or session['role'] != 'user':
        return redirect('/login')
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books")
    books = cur.fetchall()
    cur.execute("SELECT books.id, books.title, books.author, lending.borrow_date FROM books JOIN lending ON books.id = lending.book_id WHERE lending.user_id = %s", (session['user_id'],))
    borrowed_books = cur.fetchall()
    cur.close()
    return render_template('user_dashboard.html', books=books, borrowed_books=borrowed_books)

@app.route('/add_book', methods=['POST'])
def add_book():
    if 'user_id' in session and session['role'] == 'admin':
        title = request.form['title']
        author = request.form['author']
        category = request.form['category']
        available_copies = request.form['available_copies']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO books (title, author, category, available_copies) VALUES (%s, %s, %s, %s)",
                    (title, author, category, available_copies))
        mysql.connection.commit()
        cur.close()
        return redirect('/admin_dashboard')
    return redirect('/login')

@app.route('/delete_book', methods=['POST'])
def delete_book():
    if 'user_id' in session and session['role'] == 'admin':
        book_id = request.form['book_id']
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM books WHERE id=%s", (book_id,))
        mysql.connection.commit()
        cur.close()
        return redirect('/admin_dashboard')
    return redirect('/login')

@app.route('/search_books', methods=['GET'])
def search_books():
    if 'user_id' not in session or session['role'] != 'user':
        return redirect('/login')
    query = request.args.get('search_query')
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM books WHERE title LIKE %s OR author LIKE %s OR category LIKE %s",
                (f"%{query}%", f"%{query}%", f"%{query}%"))
    books = cur.fetchall()
    cur.close()
    return render_template('user_dashboard.html', books=books)

@app.route('/borrow_book', methods=['POST'])
def borrow_book():
    if 'user_id' in session and session['role'] == 'user':
        book_id = request.form['book_id']
        user_id = session['user_id']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO lending (user_id, book_id, borrow_date) VALUES (%s, %s, %s)",
                    (user_id, book_id, datetime.now()))
        cur.execute("UPDATE books SET available_copies = available_copies - 1 WHERE id = %s", (book_id,))
        mysql.connection.commit()
        cur.close()
        return redirect('/user_dashboard')
    return redirect('/login')

@app.route('/return_book', methods=['POST'])
def return_book():
    if 'user_id' in session and session['role'] == 'user':
        book_id = request.form['book_id']
        user_id = session['user_id']
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM lending WHERE user_id = %s AND book_id = %s", (user_id, book_id))
        cur.execute("UPDATE books SET available_copies = available_copies + 1 WHERE id = %s", (book_id,))
        mysql.connection.commit()
        cur.close()
        return redirect('/user_dashboard')
    return redirect('/login')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
