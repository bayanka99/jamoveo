from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages,session
import pymysql
import os
import uuid
from flask import jsonify
import json


app = Flask(__name__)
app.secret_key = os.urandom(24)


##------------------------------------------------------------------------------
##connection to the database
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
##------------------------------------------------------------------------------


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username_textbox')
        password = request.form.get('password_textbox')
        role = request.form.get('selected_role')
        instrument = request.form.get('selected_instrument') if role == 'instrument_player' else None

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
            else:
                with connection.cursor() as cursor:
                    sql = "INSERT INTO Users (username, password, role, instrument) VALUES (%s, %s, %s, %s)"
                    cursor.execute(sql, (username, password, role,instrument))
                    connection.commit()
                    flash(f"User {username} registered successfully!", "success")
        except Exception as e:
            flash(f"An error occurred: {e}", "error")
        finally:
            connection.close()
    return render_template('signup.html')


@app.route('/admin_main_page', methods=['GET', 'POST'])
def admin_main_page():
    search_result=[]
    if request.method=="POST":
        if request.form.get('select_song_button'): ##checks if the select button was clicked
            # Handle song selection
            selected_song_id = request.form.get('song_id')
            try:
                connection = get_db_connection()
                with connection.cursor() as cursor:
                    sql = "INSERT INTO selected_song (song_id) VALUES (" + selected_song_id + ")"
                    cursor.execute(sql)
                    connection.commit()
                    return redirect(url_for('live_page'))
            except Exception as e:
                flash(f"An error occurred: {e}", "error")
                return render_template('admin_main_page.html', search_results=search_result)
            finally:
                connection.close()

        # Handle search
        song_name=request.form.get('song_name_input_text')
        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                sql = "SELECT * FROM songs WHERE name LIKE '%"+song_name+"%';"
                cursor.execute(sql)
                search_result = cursor.fetchall()


            if len(search_result)==0:
                flash("nothing was found!","error")

        except Exception as e:
            flash(f"An error occurred: {e}", "error")
        finally:
            connection.close()
    return render_template('admin_main_page.html', search_results=search_result)




@app.route('/admin_signup', methods=['GET', 'POST'])
def admin_signup():
    if request.method == 'POST':
        username = request.form.get('username_text')
        password = request.form.get('password_text')
        role = request.form.get('selected_role')
        instrument = request.form.get('selected_instrument') if role == 'instrument_player' else None

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
                else:
                    sql = "INSERT INTO Users (username, password, role, instrument, is_admin) VALUES (%s,%s,%s, %s, %s)"
                    cursor.execute(sql, (username, password,role,instrument, 1))
                    connection.commit()
            return redirect(url_for('home'))
        except Exception as e:
            flash(f"An error occurread: {e}", "error")
        finally:
            connection.close()
    return render_template('admin_signup.html')


@app.route('/check_song_status')
def check_song_status():
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM selected_song")
            result = cursor.fetchone()
            if result:
                has_song = True
            else:
                has_song = False
    except Exception as e:
        return ({"error": str(e)}), 500
    finally:
        connection.close()

    return jsonify({"has_song": has_song})


@app.route('/main_page_player')
def main_page_player():
        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                #check if there is a selected song
                cursor.execute("SELECT * FROM selected_song")
                result = cursor.fetchone()
                if result:
                    return redirect(url_for('live_page'))
                else:
                    return render_template('main_page_player.html')

        except Exception as e:
            flash(f"An error occurred: {e}", "error")
        finally:
            connection.close()






@app.route('/live_page')
def live_page():
    author_name = ""
    song_name = ""
    lyrics=""
    language=""

    #this shows quit button only for admin
    curr_session= session.get('session_id')
    query = "SELECT * FROM active_sessions WHERE session_id = %s"
    connection = get_db_connection()
    with connection.cursor() as cursor:
        #check if there is a selected song
        cursor.execute(query, (curr_session,))
        user_session = cursor.fetchone()
        username=user_session[1]
        query = "SELECT * FROM Users WHERE username = %s"
        cursor.execute(query, (username,))
        user = cursor.fetchone()

        if user[5]==0: #check if not admin
            is_admin=False
        else:
            is_admin=True
    song_id = None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT song_id FROM selected_song")
            result = cursor.fetchone()

            if result:
                song_id = result[0] #retrieve the song's id
                sql_query = "select * from songs where id = %s"
                cursor.execute(sql_query,(song_id,))
                song = cursor.fetchone()
                author_name=song[2]
                song_name=song[1]
                lyrics=song[3]
                language=song[4]
                role=user[3]
                lyrics_data = json.loads(lyrics)

    except Exception as e:
        flash(f"An error occurred: {e}", "error")
    finally:
        connection.close()

    return render_template('live_page.html', author_name=author_name,song_name=song_name,is_admin=is_admin,lyrics_data=lyrics_data,language=language,user_role=role)


@app.route('/quit', methods=['POST'])
def quit():
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("Delete from selected_song;")
            connection.commit()
    except Exception as e:
        flash(f"An error occurred: {e}", "error")
    finally:
        connection.close()

    return redirect(url_for('admin_main_page'))


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
                user = cursor.fetchone()  # fetches the first matching user
            if user:
                session_id = str(uuid.uuid4()) # generate a new session ID
                session['session_id'] = session_id
                with connection.cursor() as cursor:
                    cursor.execute("INSERT INTO active_sessions (session_id, username) VALUES (%s, %s)", (session_id, username))
                    connection.commit()
                    connection.close()

                    if user[5]==0: #check if not admin
                        return redirect(url_for('main_page_player'))
                    else:
                        return redirect(url_for('admin_main_page'))

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
