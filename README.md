# Stock Exchange Simulator by Flask

StockExSim's execution example available at https://stockexsim.pythonanywhere.com/. You must register to access full scope of funcionality, please refrain from using real personal data while singing up. 

A stock shares exchange simulator built using Python's Flask framework. It contains real life update of stocks shares and its prices using an API from IEX Cloud, a a financial data infrastructure platform that connects developers and financial data creators.
It possess a simple front-end design built around bootstrap v.4 framework, and current version is fully responsive for every kind of screen. 
The app record transactions using utc-3 timezone (Buenos Aires), but can be easily adapted to any timezone by changing atributes to calls on Python's module [Pytz](https://pypi.org/project/pytz/). 

## Table of contents

* [Technologies](#technologies)

* [functionalities](#functionalities)

* [version](#version)

* [credits](#credits)


## Technologies

* [Bootstrap](https://getbootstrap.com/) v.4.6x

* [Django](https://flask.palletsprojects.com/en/1.1.x/) v.1.1.x

* [Python](https://www.python.org/) v.3.9.1

* [SQLite3](https://www.sqlite.org/) v.3.35.2


## Scope of Functionalities

* StockExSim allows user to create a free account and login storing its data in a SQL database. When a new user is created, they are asigned $10000 fake dollars to their account so they can start interacting with this stock shares market offered by the app.

* The app uses an API from [IEX Cloud](https://iexcloud.io/) that respond to user's request to access stock shares symbols, price and name of the company it represents. The API is updated in real time, so every quoting shows the current prince of every stock share at the given time.

* Registered users are allowed to quote stock shares to find out its price, buy as many as they want as long they can afford it and sell them whenever they want. There is also a track of revenue which is changed when users sell their stock to a higher/lower price that they first paid for them. 

* A log recording every transaction made by the user is also available in the app, including every piece of useful information regarding them (date, revenue, amount, type of transaction).

* There is a profile page where users can see their account info (username, email, total money, amount of succesful transactions). Also, in this sections they can change their username or password whenever they wish accessing. An option to permanently delete their account is present here too.

##  Version

This is version 1 of StockExSim, developed in mid 2020 and submitted to github on april 2021. Since its functionality is completed and has a solid design, there is not intention from part of the author to keep developing newer versions of it.

## Credits

This project was built by [locurin](https://github.com/locurin) for Github as a personal project. You can also contact me at **matiasfefernandez95@gmail.com**. 
