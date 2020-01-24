# Friendzone

Friendzone is a Flask web application that allows you to visualize current local time for all of your friends around the world, while also being able to set reminders for contacting those friends within the correct time.

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install Friendzone.

```bash
pip install requirements.txt
flask run
```

## Usage

To begin using this web app, first register as a new user. Once registered, you will be directed to the homepage.

Click "Friends" in the navigation bar and click "Add Friend". Enter in all information you wish to save.
  -Go to https://www.latlong.net/ and enter city, state, country to receive the latitude and longitude coordinates. **In full production, I would take advantage of geocoding through google maps so you could just enter your address, and it would convert to latitude and longitude. This solution is too costly at this time.
  -To get an image URL, go to the friend's Facebook profile picture, right click, and click "copy image address".
Click "Add Friend" and you will be redirected to your friends list. From there, you can click "EDIT" to update information for the friend and delete them from your application. On the home screen you will see a map with photos of your friends in their respective cities. Below the map you first see the current local time where you are located, and then your friends listed under each timezone and what time it currently is there.

Click "Reminders" in the navigation bar and click "Add Reminder". Enter in the friend, contact method, and what time (local time for their timezone) you wish to contact them. With the use of Twilio API,

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License
[MIT](https://choosealicense.com/licenses/mit/)