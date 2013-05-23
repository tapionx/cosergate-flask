CREATE TABLE IF NOT EXISTS environment (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT
);

CREATE TABLE IF NOT EXISTS user (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	surname TEXT,
	password TEXT,
	username TEXT, 
	email TEXT 
);

CREATE TABLE IF NOT EXISTS membership (
	environment INTEGER,
	user INTEGER,
	balance FLOAT
);

CREATE TABLE IF NOT EXISTS spending (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	store TEXT,
	description TEXT,
	data INTEGER,
	environment INTEGER,
	user TEXT
);

CREATE TABLE IF NOT EXISTS payment (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	amount FLOAT,
	timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	user_from TEXT,
	user_to TEXT
);

CREATE TABLE IF NOT EXISTS product (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT,
	quantity INTEGER,
	amount FLOAT,
	description TEXT ,
	barcode INTEGER ,
	spending INTEGER
);

CREATE TABLE IF NOT EXISTS utilization (
	product INTEGER,
	user TEXT
);

