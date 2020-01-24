import sqlite3
import re
import arrow
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import app, convertLat, convertLong, login_required, test_message
from PIL import Image
import urllib.request
import pytz

Session(app)

@app.route("/")
@login_required
def index():
  fmt = "ddd HH:mm"
  # 'current_time': arrow.now(row[3]).format(fmt)
  
  try:
    sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
    cursor = sqliteConnection.cursor()
    print("Connected to SQLite")

    cursor.execute("SELECT timezone FROM users WHERE id = ?", [session["user_id"]])
    time = cursor.fetchone()
    print("time: ", time)
    local_time = arrow.now(time[0]).format(fmt)
    # Query database for user
    cursor.execute("SELECT latitude, longitude, img, timezone, name FROM friends WHERE user_id = ?",
                        [session["user_id"]])
    friends = [
      {
        'lat_pct': convertLat(row[0]),
        'lon_pct': convertLong(row[1]),
        'img': row[2],
        'local_time': arrow.now(row[3]).format(fmt),
        'name': row[4]
        
      } for row in 
      cursor.fetchall()
    ]
    
    print("friends: ", friends)

    cursor.execute("SELECT timezone FROM friends WHERE user_id = ? GROUP BY timezone", [session["user_id"]])
    friendzones = [
      {
        "timezone": zone[0],
        "current_time": arrow.now(zone[0]).format(fmt),
        "friends": []
      } for zone in cursor.fetchall()
    ]
    print("friendzones: ", friendzones)

    for zone in friendzones:
      cursor.execute("SELECT name FROM friends WHERE user_id=? AND timezone = ?", [session['user_id'], zone['timezone']])
      names = cursor.fetchall()
      print('names: ', names)
      zone['friends'] = [ name[0] for name in names]

    cursor.close()
    # Redirect user to home page
    return render_template("index.html", friends=friends, local_time=local_time, friendzones=friendzones)
  except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)
  finally:
    if (sqliteConnection):
      sqliteConnection.close()
      print("The SQLite connection is closed")
  

@app.route("/register", methods=["GET", "POST"])
def register():
  """Register user"""
  if request.method == "GET":
    return render_template("register.html", timezones=pytz.all_timezones)
  else:
    data = {
      'username': request.form.get('username', ''),
      'password': request.form.get('password', ''),
      'confirmation': request.form.get('confirmation', ''),
      'timezone': request.form.get('timezone', ''),
      'phone': request.form.get('phone', ''),
      'email': request.form.get('email', '')

    }
    if not data['username']:
      return render_template("register.html",
            apology="You must enter a username", timezones=pytz.all_timezones)
    if not data['password']:
      return render_template("register.html",
              apology="You must provide password", timezones=pytz.all_timezones)
    if not data['timezone']:
      return render_template("register.html", apology="Please enter your current timezone.", timezones=pytz.all_timezones)

    # Ensure password was submitted and is complex enough      
    if not re.match(r'[A-Za-z0-9@#$%^&+=]{6,}', data['password']):
      return render_template("register.html",
              apology="Password must be at least 6 characters long and contain one uppercase and lowercase letter, one number, and one symbol",
              timezones=pytz.all_timezones)
    print("password ok")
    
    # Ensure password confirm was submitted and matches password
    if data['confirmation'] != data['password']:
      return render_template("register.html",
            apology="Password and confirm password must match",
            timezones=pytz.all_timezones)

    try:
      sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
      cursor = sqliteConnection.cursor()
      print("Connected to SQLite")
      cursor.execute("SELECT username FROM users WHERE username = ?", [data['username']])
      existing_name = cursor.fetchone()
      print("existing name: ", existing_name)

      # Ensure username was submitted and is original
      if existing_name:
        return render_template("register.html",
              apology="Username is already taken",
              timezones=pytz.all_timezones)
      print("username good")


      print("password confirm ok")
      password = generate_password_hash(data['password'])
      
      print("password ", password)


      cursor.execute("INSERT INTO users (username, hash, timezone, phone, email) VALUES (?, ?, ?, ?, ?)",
          (data["username"], password, data['timezone'], data['phone'], data['email'])
      )
      print("inserted user")
      
      cursor.execute("SELECT id, username FROM users WHERE username = ?", [data['username']])

      id_row = cursor.fetchone()
      print("row ", id_row)
      session["user_id"] = id_row[0]
      
      sqliteConnection.commit()
      cursor.close()
      # Redirect user to home page
      flash('You were successfully registered!')
      return redirect("/")

    except sqlite3.Error as error:
      print("Error while connecting to sqlite", error)
    finally:
      if (sqliteConnection):
        sqliteConnection.close()
        print("The SQLite connection is closed")

@app.route("/login", methods=["GET", "POST"])
def login():
  """Log user in"""

  # Forget any user_id
  session.clear()

  if request.method == "GET":
    return render_template("login.html")

  # User reached route via POST (as by submitting a form via POST)
  else:
    # Ensure username was submitted
    if not request.form.get("username"):
      return render_template("login.html", apology="Must provide username")
      # Ensure password was submitted
    if not request.form.get("password"):
      return render_template("login.html", apology="Must provide password")
    try:
      sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
      cursor = sqliteConnection.cursor()
      print("Connected to SQLite")

      # Query database for user
      cursor.execute("SELECT * FROM users WHERE username = ?",
                        [request.form.get("username")])
      existing_user = cursor.fetchone()
      print("existing user: ", existing_user)

      # Ensure username exists and password is correct
      if not existing_user or not check_password_hash(existing_user[2], request.form.get("password")):
        return render_template("login.html", apology="Invalid username and/or password")
      # Remember which user has logged in
      session["user_id"] = existing_user[0]
      cursor.close()
      # Redirect user to home page
      return redirect("/")
    except sqlite3.Error as error:
      print("Error while connecting to sqlite", error)
    finally:
      if (sqliteConnection):
        sqliteConnection.close()
        print("The SQLite connection is closed") 

@app.route("/logout")
def logout():
  """Log user out"""

  # Forget any user_id
  session.clear()

  # Redirect user to login form
  return redirect("/")

@app.route("/addfriend", methods=['GET', 'POST'])
@login_required
def addfriend():
  if request.method == 'GET':
    return render_template('addfriend.html', timezones=pytz.all_timezones)
  else:
    # Ensure name, latitude, longitude, and timezone were submitted
    if not request.form.get("name"):
      return render_template("addfriend.html",
          apology="You must enter a name",
          timezones=pytz.all_timezones)
    if not request.form.get("latitude"):
      return render_template("addfriend.html",
          apology="You must enter a latitude",
          timezones=pytz.all_timezones)
    if not request.form.get("longitude"):
      return render_template("addfriend.html",
          apology="You must enter a longitude",
          timezones=pytz.all_timezones)
    if request.form.get("timezone") == "Choose...":
      return render_template("addfriend.html",
          apology="You must enter a timezone",
          timezones=pytz.all_timezones)
    if not request.form.get("img"):
      return render_template("addfriend.html",
          apology="You must enter an image URL",
          timezones=pytz.all_timezones)
          
    try:
      sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
      cursor = sqliteConnection.cursor()
      print("Connected to SQLite")
      # Insert into friends table
      cursor.execute(
        "INSERT INTO friends (user_id, name, email, birthday, phone, address, timezone, latitude, longitude, img) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
          (
            session['user_id'],
            request.form.get("name"),
            request.form.get("email"),
            request.form.get("birthday"),
            request.form.get("phone"),
            request.form.get("address"),
            request.form.get("timezone"),
            request.form.get("latitude"),
            request.form.get("longitude"),
            request.form.get("img")
          )
      )
      friends = cursor.fetchall()

      print("friends: ", friends)
      sqliteConnection.commit()
      cursor.close()
      return redirect('/friendlist')

    except sqlite3.Error as error:
      print("Error while connecting to sqlite", error)
    finally:
      if (sqliteConnection):
        sqliteConnection.close()
        print("The SQLite connection is closed")

@app.route("/update/<int:id>", methods=['GET', 'POST'])
@login_required
def updateFriend(id):
  if request.method == 'GET':
    try:
      sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
      cursor = sqliteConnection.cursor()
      print("Connected to SQLite", id, session['user_id'])
      cursor.execute("SELECT name, email, birthday, phone, timezone, latitude, longitude, img FROM friends WHERE user_id = ? AND id = ?", [session["user_id"], id])
      friend = cursor.fetchone()
      print("friend: ", friend)

      cursor.close()
      return render_template('updatefriend.html', friend=friend, timezones=pytz.all_timezones, id=id)

    except sqlite3.Error as error:
      print("Error while connecting to sqlite", error)
    finally:
      if (sqliteConnection):
        sqliteConnection.close()
        print("The SQLite connection is closed")
    
  else:
    try:
      sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
      cursor = sqliteConnection.cursor()
      print("Connected to SQLite")
      # Update friends table
      cursor.execute(
        "UPDATE friends SET name = ?, email = ?, birthday = ?, phone = ?, timezone = ?, latitude = ?, longitude = ?, img = ? WHERE id = ? AND user_id = ?",
          (
            request.form.get("name"),
            request.form.get("email"),
            request.form.get("birthday"),
            request.form.get("phone"),
            request.form.get("timezone"),
            request.form.get("latitude"),
            request.form.get("longitude"),
            request.form.get("img"),
            id,
            session['user_id']
          )
      )
      friends = cursor.fetchall()

      print("friends: ", friends)
      sqliteConnection.commit()
      cursor.close()
      return redirect('/friendlist')

    except sqlite3.Error as error:
      print("Error while connecting to sqlite", error)
    finally:
      if (sqliteConnection):
        sqliteConnection.close()
        print("The SQLite connection is closed")

@app.route("/delete/<int:id>", methods=['GET', 'POST'])
@login_required
def deleteFriend(id):

  if request.method == "POST":
    
    try:
      sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
      cursor = sqliteConnection.cursor()
      print("Connected to SQLite")
      cursor.execute("DELETE FROM friends WHERE user_id = ? AND id = ?", [session["user_id"], id])
      sqliteConnection.commit()
      cursor.close()
      return redirect('/friendlist')
    except sqlite3.Error as error:
      print("Error while connecting to sqlite", error)
    finally:
      if (sqliteConnection):
        sqliteConnection.close()
        print("The SQLite connection is closed")

@app.route("/friendlist")
@login_required
def friendlist():
  try:
    sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
    cursor = sqliteConnection.cursor()
    print("Connected to SQLite")
    # Query database for user
    cursor.execute("SELECT * FROM friends WHERE user_id = ?", [session['user_id']])
    friends = cursor.fetchall()
    data = []
    for friend in friends:
      id = friend[0]
      name = friend[2]
      email = friend[3]
      birthday = friend[4]
      phone = friend[5]
      data.append({
        'id': id,
        'name': name,
        'email': email,
        'birthday': birthday,
        'phone': phone,
      })

    cursor.close()
    return render_template('friends.html', data=data)

  except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)
  finally:
    if (sqliteConnection):
      sqliteConnection.close()
      print("The SQLite connection is closed")

@app.route("/addreminder", methods=['GET', 'POST'])
@login_required
def addreminder():

  if request.method == 'GET':
    try:
      sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
      cursor = sqliteConnection.cursor()
      print("Connected to SQLite")
      cursor.execute("SELECT id, name FROM friends WHERE user_id = ?", [session["user_id"]])
      friends = cursor.fetchall()
      data = []
      for friend in friends:
        id = friend[0]
        name = friend[1]
        data.append({
          'id': id,
          'name': name,
        })
      return render_template('addreminder.html', data=data)
    except sqlite3.Error as error:
      print("Error while connecting to sqlite", error)
    finally:
      if (sqliteConnection):
        sqliteConnection.close()
        print("The SQLite connection is closed")
  else:
    try:
      sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
      cursor = sqliteConnection.cursor()
      print("Connected to SQLite")
      friend_id = request.form.get('id')
      friend_time = request.form.get('time')

      cursor.execute("SELECT timezone FROM friends WHERE id = ? AND user_id = ?", [friend_id, session["user_id"]])
      friend_tz = cursor.fetchone()[0]

      friend_time_obj = arrow.get(friend_time)
      friend_time_obj = friend_time_obj.replace(tzinfo=friend_tz)
      utc_time = friend_time_obj.to('utc')

      # Insert into friends table
      cursor.execute(
        "INSERT INTO reminders (user_id, friend_id, contact_method, time_gmt) VALUES (?, ?, ?, ?)",
          (
            session['user_id'],
            friend_id,
            request.form.get('contact_method'),
            utc_time.strftime('%Y-%m-%d %H:%M:%S')
          )
      )

      sqliteConnection.commit()
      cursor.close()
      return redirect('/reminders')

    except sqlite3.Error as error:
      print("Error while connecting to sqlite", error)
    finally:
      if (sqliteConnection):
        sqliteConnection.close()
        print("The SQLite connection is closed")

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.route("/reminders")
@login_required
def reminders():
  
  try:
    sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
    sqliteConnection.row_factory = dict_factory
    cursor = sqliteConnection.cursor()
    print("Connected to SQLite")
    # Query database for user
    cursor.execute("""
      SELECT reminders.time_gmt AS time, reminders.contact_method, friends.name, friends.timezone as friend_tz, reminders.sent
      FROM reminders
      JOIN friends
      ON friends.id = reminders.friend_id
      WHERE reminders.user_id = ?
      ORDER BY reminders.time_gmt DESC
    """, [session['user_id']])

    reminders = [
      dict(row,
        reminder_time_local=arrow.get(row['time']).to(row['friend_tz'])
      ) for row in cursor.fetchall()
    ]

    print("all reminders: ", reminders)

    cursor.close()
    return render_template('reminders.html', reminders=reminders)

  except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)
  finally:
    if (sqliteConnection):
      sqliteConnection.close()
      print("The SQLite connection is closed")

@app.route("/profile")
@login_required
def profile():
  try:
    sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
    cursor = sqliteConnection.cursor()
    print("Connected to SQLite")
    # Query database for user
    cursor.execute("SELECT * FROM users WHERE id = ?", [session['user_id']])
    user = cursor.fetchone()
    

    cursor.close()
    return render_template('profile.html', user=user)

  except sqlite3.Error as error:
    print("Error while connecting to sqlite", error)
  finally:
    if (sqliteConnection):
      sqliteConnection.close()
      print("The SQLite connection is closed")

@app.route("/profile/edit", methods=['GET', 'POST'])
@login_required
def updateProfile():
  if request.method == 'GET':
    try:
      sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
      cursor = sqliteConnection.cursor()
      print("Connected to SQLite", session['user_id'])
      cursor.execute("SELECT username, email, phone, timezone FROM users WHERE id = ?", [session["user_id"] ])
      user = cursor.fetchone()
      print("user: ", user)

      cursor.close()

      return render_template('updateprofile.html', user=user, timezones=pytz.all_timezones,)

    except sqlite3.Error as error:
      print("Error while connecting to sqlite", error)
    finally:
      if (sqliteConnection):
        sqliteConnection.close()
        print("The SQLite connection is closed")
  else:
    try:
      sqliteConnection = sqlite3.connect('friendzone.db', timeout=20)
      cursor = sqliteConnection.cursor()
      print("Connected to SQLite")
      # Update friends table
      cursor.execute(
        "UPDATE users SET username = ?, email = ?, phone = ?, timezone = ? WHERE id = ?",
          (
            request.form.get("username"),
            request.form.get("email"),
            request.form.get("phone"),
            request.form.get("timezone"),
            session['user_id']
          )
      )

      sqliteConnection.commit()
      cursor.close()
      return redirect('/profile')

    except sqlite3.Error as error:
      print("Error while connecting to sqlite", error)
    finally:
      if (sqliteConnection):
        sqliteConnection.close()
        print("The SQLite connection is closed")
