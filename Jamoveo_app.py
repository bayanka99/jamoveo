from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages,session
import pymysql
import os
import uuid


app = Flask(__name__)
app.secret_key = os.urandom(24)


DB_HOST = os.getenv('DB_HOST', 'bayanka.mysql.pythonanywhere-services.com')
DB_USER = os.getenv('DB_USER', 'bayanka')
DB_PASS = os.getenv('DB_PASS', 'adminadmin')
DB_NAME = os.getenv('DB_NAME', 'bayanka$jamoveo_db')

def get_db_connection():
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASS,
        database=DB_NAME
    )
    return connection


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        instrument = request.form.get('instrument') if role == 'instrument_player' else None

        if not username or not password or not role:
            flash("All fields are required!", "error")
            return redirect(url_for('signup'))

        if role == 'instrument_player' and not instrument:
            flash("Instrument is required for instrument players!", "error")
            return redirect(url_for('signup'))


        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                sql = "SELECT * FROM Users WHERE username = %s"
                cursor.execute(sql, (username,))
                existing_user = cursor.fetchone()

            if existing_user:
                flash("Username already exists. Please choose a different username.", "error")
                return redirect(url_for('signup'))

            with connection.cursor() as cursor:
                sql = """
                INSERT INTO Users (username, password, role, instrument)
                VALUES (%s, %s, %s, %s)
                """
                cursor.execute(sql, (username, password, role,instrument))
                connection.commit()
            connection.close()
            flash(f"User {username} registered successfully!", "success")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
        return redirect(url_for('signup'))
    return render_template('signup.html')


@app.route('/admin_signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')
        instrument = request.form.get('instrument') if role == 'instrument_player' else None

        if not username or not password or not role:
            flash("All fields are required!", "error")
            return redirect(url_for('admin_signup'))

        if role == 'instrument_player' and not instrument:
            flash("Instrument is required for instrument players!", "error")
            return redirect(url_for('admin_signup'))

        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                # check if the user already exists
                cursor.execute("SELECT * FROM Users WHERE username = %s", (username,))
                if cursor.fetchone():
                    flash("User already exists!", "error")
                    return redirect(url_for('admin_signup'))


                # check if there is already an admin
                cursor.execute("SELECT COUNT(*) FROM Users WHERE is_admin = %s", (1,))
                admin_count = cursor.fetchone()[0]

                if admin_count > 0:
                    flash("An admin already exists. Only one admin is allowed.", "error")
                    return redirect(url_for('admin_signup'))


                sql = "INSERT INTO Users (username, password, role, instrument, is_admin) VALUES (%s,%s,%s, %s, %s)"
                cursor.execute(sql, (username, password,role,instrument, 1))
                connection.commit()
            connection.close()
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
        return redirect(url_for('admin_signup'))
    return render_template('admin_signup.html')


@app.route('/main_page_player')
def main_page_player():
    return render_template('main_page_player.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # check if user already logged in
        connection = get_db_connection()
        with connection.cursor() as cursor:
            sql = "SELECT EXISTS(SELECT 1 FROM active_sessions WHERE username = %s)"
            cursor.execute(sql, (username,))
            result = cursor.fetchone()
            if result[0] == 1:
                flash(f"{username} is already logged in.", "error")
                return redirect(url_for('login'))

        if not username or not password:
            flash("Username and password are required!", "error")
            return redirect(url_for('login'))

        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                sql = "SELECT * FROM Users WHERE username = %s AND password = %s"
                cursor.execute(sql, (username, password))
                user = cursor.fetchone()  # Fetch the first matching user
            if user:
                session_id = str(uuid.uuid4()) # generate a new session ID
                session['session_id'] = session_id
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO active_sessions (session_id, username) VALUES (%s, %s)", (session_id, username))
                    connection.commit()
                    connection.close()
                return redirect(url_for('main_page_player'))
            else:
                flash("Invalid username or password. Please try again.", "error")
                connection.close()
                return redirect(url_for('login'))
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
            connection.close()
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM active_sessions WHERE session_id = %s", (session.get('session_id'),))
            connection.commit()
        session.pop('session_id', None)
        return redirect(url_for('home'))

    finally:
        connection.close()





if __name__ == '__main__':
    app.run(debug=True)
