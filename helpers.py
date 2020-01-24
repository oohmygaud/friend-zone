from flask import redirect, session
from functools import wraps
from twilio.rest import Client
import sqlite3
import arrow
from flask import Flask, render_template, request, session
from tempfile import mkdtemp
from flask_mail import Mail, Message
import os

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"


mail_settings = {
    "MAIL_SERVER": 'email-smtp.us-east-1.amazonaws.com',
    "MAIL_PORT": 465,
    "MAIL_USE_TLS": False,
    "MAIL_USE_SSL": True,
    "MAIL_USERNAME": os.environ['EMAIL_USER'],
    "MAIL_PASSWORD": os.environ['EMAIL_PASSWORD']
}

app.config.update(mail_settings)
mail = Mail(app)


def sendEmail(to_email, msg):
  with app.app_context():
    msg = Message(subject="Hello",
                  sender="noreply@netprophet.tech",
                  recipients=[to_email],
                  body=msg)
    mail.send(msg)


def convertLat(lat):
    return (1 - (lat - 15 + 90) / 180) * 100


def convertLong(long):
    return (long - 14.4 + 180) / 360 * 100


def login_required(f):
    """
    Decorate routes to require login.
    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def test_message(to_phone, msg):
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_ACCOUNT_AUTH']
    client = Client(account_sid, auth_token)

    for char in '- ()_':
        to_phone = to_phone.replace(char, '')

    message = client.messages \
        .create(
            body=msg,
            from_='+16182074142',
            to='+1%s' % to_phone
        )

    return (message.sid)


def send_reminder_by_id(id):
    try:
        sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")

        # Query database

        QUERY = """
          SELECT users.phone, friends.name, friends.timezone, reminders.contact_method, users.email
          FROM reminders
          JOIN friends on friends.id = reminders.friend_id
          JOIN users on users.id = reminders.user_id
          WHERE datetime('now') > time_gmt AND sent IS NOT 1 AND reminders.id = ?;
          """
        cursor.execute(QUERY, [id])
        reminder = cursor.fetchone()
        print("all reminders to send: ", reminder)

        # return none if sent=true or not due
        if not reminder:
            return None

        # update sent=true
        cursor.execute("UPDATE reminders SET sent = 1 WHERE id = ? ", [id])
        sqliteConnection.commit()
        cursor.close()

        MSG = "It's now %s in %s, don't forget to call %s!" % (
            arrow.now(reminder[2]).format(
                'ddd HH:mm'), reminder[2], reminder[1]
        )

        # send message
        print('Notify', reminder[3])
        if reminder[3] == 'Email':
          return sendEmail(reminder[4], MSG)
        else:
          return test_message(reminder[0], MSG)

    except sqlite3.Error as error:
        print("Error while connecting to sqlite", error)
    finally:
        if (sqliteConnection):
            sqliteConnection.close()
            print("The SQLite connection is closed")


def get_due_reminders():
    # return [id for reminders if date < now and sent=false]

    try:
        sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
        cursor = sqliteConnection.cursor()
        print("Connected to SQLite")

        # Query database

        QUERY = """
    SELECT reminders.id, friends.timezone, reminders.contact_method, friends.name
    FROM reminders
    JOIN friends on friends.id = reminders.friend_id
    JOIN users on users.id = reminders.user_id
    WHERE datetime('now') > time_gmt AND sent IS NOT 1;
    """
        cursor.execute(QUERY)
        reminders = cursor.fetchall()
        cursor.close()

        # return none if sent=true or not due
        if not reminders:
            return []
        return [
            {
                'reminder_id': r[0],
                'friend_timezone': r[1],
                'contact_method': r[2],
                'friend_name': r[3]
            }
            for r in reminders
        ]
    except Exception as e:
        print(e)
        return []


def send_all_due_reminders():
    # for id in due_reminders: send_reminder_by_id()
    for reminder in get_due_reminders():
        print('due', reminder)
        print(send_reminder_by_id(reminder['reminder_id']))
