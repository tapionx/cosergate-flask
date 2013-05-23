from flask import Flask, g, session, request, redirect, url_for, jsonify, abort, render_template
import sqlite3
import os
import re

app = Flask(__name__)

# DATABASE

DATABASE = os.path.dirname(os.path.abspath(__file__)) + '/cosergate.sqlite3'

def connect_db():
    return sqlite3.connect(DATABASE)

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    if hasattr(g, 'db'):
        g.db.close()

def query_db(query, args=(), one=False):
    cur = g.db.execute(query, args)
    rv = [dict((cur.description[idx][0], value)
               for idx, value in enumerate(row)) for row in cur.fetchall()]
    return (rv[0] if rv else None) if one else rv

# UTILITIES

def get_n_users(environment):
	return query_db('SELECT COUNT(u.id) AS n \
					 FROM user AS u, membership AS m \
					 WHERE m.environment = ? AND m.user = u.id',
					 [environment], one=True)['n']

def get_users(environment):
	return query_db('SELECT u.username, u.name, u.surname, u.email, u.id, m.balance \
			         FROM user AS u, membership AS m \
			         WHERE m.environment = ? AND m.user = u.id',
					[environment])

def get_spendings(environment):
	spendings = query_db('SELECT * FROM spending WHERE environment = ?',
						[environment])
	for i in range(len(spendings)):
		spendings[i]['products'] = query_db('SELECT * FROM product WHERE spending = ?',
											[spendings[i]['id']])
		for k in range(len(spendings[i]['products'])):
			users = query_db('SELECT user FROM utilization WHERE product = ?',
				   		    [spendings[i]['products'][k]['id']])
			user_list = []
			for user in users:
				user_list.append(user['user'])
			spendings[i]['products'][k]['utilizations'] = user_list
	return spendings

def post_spending_to_dict(spending):
	d = {}
	d['user'] = spending['user']
	d['store'] = spending['store']
	d['description'] = spending['description']
	d['data'] = spending['data']
	d['products'] = []
	for k in range(1, int(spending['nproducts'])+1):
		product = {}
		product['name'] = spending['p['+str(k)+'][name]']
		product['quantity'] = spending['p['+str(k)+'][quantity]']
		product['amount'] = spending['p['+str(k)+'][amount]']
		product['description'] = spending['p['+str(k)+'][description]']
		product['users'] = []
		nusers = get_n_users(session['environment'])
		for i in range(1, nusers+1):
			if spending.has_key('p['+str(k)+'][user]['+str(i)+']'):
				product['users'].append(i)
		d['products'].append(product)
	return d

# VIEWS

@app.errorhandler(404)
def page_not_found(error):
    return '404 NOT FOUND', 404

@app.route('/')
def home():
	if 'logged' in session:
		users = get_users(session['environment'])
		spendings = get_spendings(session['environment'])
		return render_template('main.html', users=users, spendings=spendings)
	return '''
		<h1>Benvenuto nel fantastico Cosergate r.e.l.o.a.d.e.d.</h1>
		<form action="/login" method="post">
			<p><input type=text name=username placeholder="username">
			<p><input type="password" name=password placeholder="password">
			<p><input type=submit value=Login>
		</form>
	'''

@app.route('/list')
def list():
	if 'logged' not in session:
		abort(404)
	users = get_users(session['environment'])
	spendings = get_spendings(session['environment'])
	return jsonify(spendings=spendings, users=users)
	
@app.route('/login', methods=['POST'])
def login():
	username = request.form['username']
	password = request.form['password']
	user = query_db('SELECT * FROM user WHERE username = ? AND password = ?', [username, password], one=True)
	if user is None:
		return 'login incorrect'
	else:
		session['user'] = user
		session['logged'] = True
		environment = query_db('SELECT environment FROM membership WHERE user = ?',
								[user['id']], one=True)
		session['environment'] = environment['environment']
		return redirect('/')
    
@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('logged', False)
    return redirect('/')

@app.route('/new_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'GET':
        return '''
			<form action="" method="POST">
				<p><input type="text" name="name" placeholder="name" /></p>
				<p><input type="text" name="surname" placeholder="surname" /></p>
				<p><input type="text" name="username" placeholder="username" /></p>
				<p><input type="password" name="password" placeholder="password" /></p>
				<p><input type="text" name="email" placeholder="email" /></p>
				<p><input type="submit" name="registrati" /></p>
			</form>
		'''
    if request.method == 'POST':
		name = request.form['name']
		if not name.isalpha():
			return 'name must be only alphabetic'
		surname = request.form['surname']
		if not surname.isalpha():
			return 'surname must be only alphabetic'
		username = request.form['username']
		if not username.isalnum():
			return 'username must be alphanumeric'
		password = request.form['password']

		email = request.form['email']
		if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
			return 'mail must be valid mail address'
		# check if user already exists
		user = query_db('SELECT * FROM user WHERE email = ?',
                [email], one=True)
		if user is not None:
			return 'user already exist'
		g.db.execute('INSERT INTO user (name, surname, username, password, email) VALUES (?,?,?,?,?)',
				[name, surname, username, password, email])
		g.db.commit()
		return 'nuovo utente aggiunto con successo'

@app.route('/new_spending', methods=['POST'])
def new_spending():
	s = post_spending_to_dict(request.form)
	c = g.db.cursor()
	c.execute('INSERT INTO spending (store, description, data, environment, user) VALUES (?,?,?,?,?)',
				[s['store'], s['description'], s['data'], session['environment'], s['user']])
	spending_id = c.lastrowid
	for p in s['products']:
		c.execute('INSERT INTO product (name, quantity, amount, description, spending) VALUES (?,?,?,?,?)',
					[p['name'], p['quantity'], p['amount'], p['description'], spending_id])
		product_id = c.lastrowid
		for u in p['users']:
			c.execute('INSERT INTO utilization (product, user) VALUES (?,?)',
						[product_id, u])
	g.db.commit()
	#return str(request.form)
	return jsonify(spending=s)
		
app.secret_key = 's9d8fg456tr5h1sfg21h3fg5h6ktu8i9turtyr4fh6g54'

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

