from flask import Flask, render_template, request, redirect, url_for
from pymongo.mongo_client import MongoClient
from pymongo.errors import ConnectionFailure
#import pymysql
#import os


app = Flask(__name__)


MONGO_URI = 'mongodb+srv://bayanka:admin@jamoveo.pskun.mongodb.net/?retryWrites=true&w=majority&appName=JaMoveo'
# DB_HOST = os.getenv('DB_HOST', 'bayanka.mysql.pythonanywhere-services.com')
# DB_USER = os.getenv('DB_USER', 'bayanka')
# DB_PASS = os.getenv('DB_PASS', 'adminadmin')
# DB_NAME = os.getenv('DB_NAME', 'bayanka$jamoveo_db')

# def get_db_connection():
#     connection = pymysql.connect(
#         host=DB_HOST,
#         user=DB_USER,
#         password=DB_PASS,
#         database=DB_NAME
#     )
#     return connection

# Create a new client and connect to the server
client = MongoClient(MONGO_URI)
# Send a ping to confirm a successful connection
try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e)

db = client['JaMoveo']  # Replace with your database name
users_collection = db['Users']

@app.route('/')
def home():
    return render_template('signup.html')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    instrument = request.form.get('instrument')

    # Simple validation
    if not username or not password or not instrument:
        return redirect(url_for('home'))

    user_data = {
        'username': username,
        'password': password,
        'instrument': instrument
    }

    try:
        users_collection.insert_one(user_data)
    except Exception as e:
        return f"An error occurred: {e}"

    return f"User {username} registered successfully!"
    # try:
    #     connection = get_db_connection()
    #     with connection.cursor() as cursor:
    #         sql = "INSERT INTO users (username, password, instrument) VALUES (%s, %s, %s)"
    #         cursor.execute(sql, (username, password, instrument))
    #         connection.commit()
    #     connection.close()
    # except Exception as e:
    #     return f"An error occurred: {e}"

    # return f"User {username} registered successfully!"



if __name__ == '__main__':
    app.run(debug=True)
