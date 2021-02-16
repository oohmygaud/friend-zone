# Friendzone

Friendzone is a Flask web application that allows you to visualize current local time for all of your friends around the world, while also being able to set reminders for contacting those friends within the correct time.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install Friendzone; currently python3.7 is supported.

```bash
pip3 install -r requirements.txt
```

## Usage

### Launching the Webapp for Testing/Development

```bash
flask run
```

### Using the Webapp

To begin using this web app, first register as a new user. Once registered, you will be directed to the homepage.

Click "Friends" in the navigation bar and click "Add Friend". Enter in all information you wish to save.

  - Go to https://www.latlong.net/ and enter city, [state], country to receive the latitude and longitude coordinates. **In full production, I would take advantage of geocoding through google maps so you could just enter your address, and it would convert to latitude and longitude. This solution is too costly at this time.
  - To get an image URL, go to the friend's Facebook profile picture, right click, and click "copy image address".

Click "Add Friend" and you will be redirected to your friends list. From there, you can click "EDIT" to update information for the friend and delete them from your application. On the home screen you will see a map with photos of your friends in their respective cities. Below the map you first see the current local time where you are located, and then your friends listed under each timezone and what time it currently is there.

Click "Reminders" in the navigation bar and click "Add Reminder". Enter in the friend, contact method by which you would like to be contacted, and what time (local time for their timezone) you wish to contact them.

### Delivering Reminders



#### Twilio API + Email credentials
The following shell variables must be set to use the Twilio API to deliver SMS reminders and SMTP emails:

```bash
export TWILIO_ACCOUNT_AUTH=....
export TWILIO_ACCOUNT_SID=....
export EMAIL_USER=....
export EMAIL_PASSWORD=....
export EMAIL_SMTP_HOST=....
```

You can put the above lines into a file named `.local_env`; for your convenience, this project includes a `.envrc` file incase you have `direnv` installed, which will automatically `source .local_env` every time you `cd` into the `friend_zone/` directory. If you don't have `direnv` installed in your shell, just make sure you `source .local_env`, or otherwise export these variables, prior to running the `send_forever.py` jobs below.

#### Run the Daemon OR Set Up A Cronjob

To run the daemon for development, in a new terminal run:
```bash
python3 send_forever.py
```

You can also schedule this service using `systemctl`, `supervisord` or `init.d`.

If running a permanent service isn't suitable for you, we've also provided `send_once.py` which is suitable for running in a cronjob, at any interval you wish (upon each run, it will send all overdue notifications).


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License
This project is made available under the [MIT](https://choosealicense.com/licenses/mit/) license.