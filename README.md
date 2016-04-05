Hackathon-kit
===========



#### Setup your own instance

- Create Heroku account
[![Deploy](https://www.herokucdn.com/deploy/button.png)](https://heroku.com/deploy)

- Create Twilio Account
- Buy a number that has support for SMS and Voice ($1 a month)
- Go to Phone Numbers -> Manage -> Click your phone number
- Input the two urls as shown in the image below, replacing the domain with the location of your Heroku app.
![](http://teachthe.net/topclipbox/2016-04-05_23-12-07PZCAFG.png)

##### Development Info
```
- Install git
- Install python 2.7.6
- Install pip (e.g. sudo easy_install pip)
<clone our app to a local git repository>
$ sudo pip install -r requirements.txt
```

Create new migrations
```
$ python manage.py makemigrations
```

Run migrations
```
$ python manage.py migrate
```

Run Server
```
$ python manage.py runserver
Visit http://127.0.0.1:8000/static/index.html
```

Admin Panel: Create a superuser
```
$ python manage.py createsuperuser
Visit http://127.0.0.1:8000/admin/
```

Make it so everytime you push to Github, Heroku rebuilds server with latest code
```
- Login to Heroku
- Click on your application
- Click DEPLOY
- Under Deployment Method, click Github (Connect to Github) and follow instructions
```