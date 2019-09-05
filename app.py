from flask import Flask, render_template, flash, redirect, url_for, session, request, logging
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, SelectField
from flask_mysqldb import MySQL
from functools import wraps
from flask_uploads import UploadSet, configure_uploads, IMAGES, patch_request_class
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import sha256_crypt, pbkdf2_sha256
import os
from wtforms.fields.html5 import EmailField
from flask_mail import Mail, Message
import psycopg2



app = Flask(__name__)
mysql = SQLAlchemy(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://dwxxiixwimclsh:f6b47c911dfe932eae6c8af844e46ce0453163fdfcdd18a6a1170f77e21be035@ec2-54-235-86-101.compute-1.amazonaws.com:5432/d2si4i4gr4idrn'
DATABASE_DEFAULT = 'postgresql://postgres:f6b47c911dfe932eae6c8af844e46ce0453163fdfcdd18a6a1170f77e21be035@ec2-54-235-86-101.compute-1.amazonaws.com:5432/register'


# Initialize the app for use with this MySQL class
mysql.init_app(app)
 
@app.route('/')
def home():
	return render_template('home.html')



def not_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged' in session:
            return redirect(url_for('page'))
        else:
            return f(*args, *kwargs)

    return wrap
class LoginForm(Form):  # Create Login Form
    username = StringField('', [validators.length(min=1)],
                           render_kw={'autofocus': True, 'placeholder': 'Username'})
    password = PasswordField('', [validators.length(min=3)],
                             render_kw={'placeholder': 'Password'})
def is_admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' in session:
            return f(*args, *kwargs)
        else:
            return redirect(url_for('users'))

    return wrap


def not_admin_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'admin_logged_in' in session:
            return redirect(url_for('users'))
        else:
            return f(*args, *kwargs)

    return wrap


def wrappers(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)

    return wrapped


@app.route('/page_edit', methods=['POST', 'GET'])
@is_admin_logged_in
def page_edit():
    if request.method == 'POST':
        description = request.form['description']
        file = request.files['picture']
        if description and file:
            pic = file.filename
            photo = pic.replace("'", "")
            picture = photo.replace(" ", "_")
            if picture.lower().endswith(('.png', '.jpg', '.jpeg')):
                curs = mysql.connection.cursor()
                curs.execute("INSERT INTO added(description, picture)"
                            "VALUES(%s, %s)",
                            (description, picture))
                mysql.connection.commit()
                curs.close()
                flash(' successful', 'success')
                return redirect(url_for('page_edit'))
    return render_template('pages/page_edit.html')

@app.route('/login', methods= ["GET", "POST"])
def login():
	form = LoginForm(request.form)
	if request.method == 'POST' and form.validate():
		username = form.username.data
		passwordata = form.password.data
		cur = mysql.connection.cursor()
		result = cur.execute("SELECT * FROM users WHERE username=%s", [username])

		if result > 0:
			data = cur.fetchone()
			password = data['password']
			uid = data['id']
			name = data['name']
		
			if passwordata == password:
				session['logged'] = True
				session['uid'] = uid

				session['s_name'] = name
				
				x = '1'
				cur.execute("UPDATE users SET online=%s WHERE id=%s", (x, uid))
				flash('You are logged in', 'success')
				return redirect(url_for('page'))
			else:
				flash('Incorrect password', 'danger')
				return render_template('login.html', form=form)

		else:
			flash('invalid Username', 'danger')

			cur.close()
			return render_template('login.html', form=form)

	return render_template('login.html')

@app.route('/page')
def page():

    curso = mysql.connection.cursor()
    users_rows = curso.execute("SELECT * FROM users")
    added_rows = curso.execute("SELECT * FROM added")
    result = curso.fetchall()
    curso.close()
    return render_template('page.html', result=result,
                           users_rows=users_rows, added_rows=added_rows)


@app.route('/logout')
def logout():
        session.clear()
        x = "0"
        flash('You are logged out', 'success')
        return redirect(url_for('home'))
    




@app.route('/register', methods= ["GET", "POST"])
def register():
	if request.method == "POST":
		name = request.form.get("name")
		username = request.form.get("username")
		password = request.form.get("password")
		confirm = request.form.get("confirm")
		

		if password == confirm:


			cur = mysql.connection.cursor()
			cur.execute("INSERT INTO users(name, username, password) VALUES(%s, %s, %s)",
                    (name, username, password))
			mysql.connection.commit()
			cur.close()
			flash("you have successfully registered", "success")
			return redirect(url_for('login'))

		else:
			flash("password does not match", "danger")
			return render_template("register.html")
 


	return render_template('register.html')

class MessageForm(Form):  # Create Message Form
    body = StringField('', [validators.length(min=1)], render_kw={'autofocus': True})

@app.route('/chatting/<string:id>', methods=['GET', 'POST'])
def chatting(id):
    if 'uid' in session:
        form = MessageForm(request.form)
        # Create cursor
        cur = mysql.connection.cursor()

        # lid name
        get_result = cur.execute("SELECT * FROM users WHERE id=%s", [id])
        l_data = cur.fetchone()
        if get_result > 0:
            session['name'] = l_data['name']
            uid = session['uid']
            session['lid'] = id

            if request.method == 'POST' and form.validate():
                txt_body = form.body.data
                # Create cursor
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO messages(body, msg_by, msg_to) VALUES(%s, %s, %s)",
                            (txt_body, id, uid))
                # Commit cursor
                mysql.connection.commit()

            # Get users
            cur.execute("SELECT * FROM users")
            users = cur.fetchall()

            # Close Connection
            cur.close()
            return render_template('chat_room.html', users=users, form=form)
        else:
            flash('No permission!', 'danger')
            return redirect(url_for('index'))
    else:
        return redirect(url_for('login'))
@app.route('/chatt', methods=['GET', 'POST'])
def chatt():
	if 'lid' in session:
		id = session['lid']
		uid = session['uid']
		cur = mysql.connection.cursor()
		cur.execute("SELECT * FROM messages WHERE (msg_by=%s AND msg_to=%s) OR (msg_by=%s AND msg_to=%s) "
                    "ORDER BY id ASC", (id, uid, uid, id))
		chats = cur.fetchall()

		cur.close()
		return render_template('chats.html', chats=chats, )
	return render_template('chat1.html')


@app.route('/chats', methods=['GET', 'POST'])
def chats():
    if 'lid' in session:
        id = session['lid']
        uid = session['uid']
        # Create cursor
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM messages WHERE (msg_by=%s AND msg_to=%s) OR (msg_by=%s AND msg_to=%s) "
        			"ORDER BY id ASC", (id, uid, uid, id))
        chats = cur.fetchall()
        cur.close()
        return render_template('chats.html', chats=chats, )
    return redirect(url_for('login'))

@app.route('/users')
@is_admin_logged_in
def users():
    curso = mysql.connection.cursor()

    users_rows = curso.execute("SELECT * FROM users")
    added_rows = curso.execute("SELECT * FROM added")
    result = curso.fetchall()
    return render_template('pages/all_users.html', result=result,
                           users_rows=users_rows, added_rows=added_rows)

@app.route('/admin_login', methods=['GET', 'POST'])
@not_admin_logged_in
def admin_login():
    if request.method == 'POST':
        # GEt user form
        username = request.form['email']
        password_candidate = request.form['password']

        # Create cursor
        cur = mysql.connection.cursor()

        # Get user by username
        result = cur.execute("SELECT * FROM admin WHERE email=%s", [username])

        if result > 0:
            # Get stored value
            data = cur.fetchone()
            password = data['password']
            uid = data['id']
            name = data['firstName']

            # Compare password
            if password_candidate == password :
                # passed
                session['admin_logged_in'] = True
                session['admin_uid'] = uid
                session['admin_name'] = name

                return redirect(url_for('users'))

            else:
                flash('Incorrect password', 'danger')
                return render_template('pages/login.html')

        else:
            flash('Username not found', 'danger')
            # Close connection
            cur.close()
            return render_template('pages/login.html')
    return render_template('pages/login.html')
@app.route('/myadmin')
def myadmin():
	curso = mysql.connection.cursor()
	users_rows = curso.execute("SELECT * FROM users")
	result = curso.fetchall()
	return render_template('crud.html', result=result,
                           users_rows=users_rows)

@app.route('/admin_out')
def admin_logout():
    if 'admin_logged_in' in session:
        session.clear()
        return redirect(url_for('admin_login'))
    return redirect(url_for('admin'))

@app.route('/insert', methods = ['POST'])
def insert():

    if request.method == "POST":
        flash("Data Inserted Successfully", "success")
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        cur = mysql.connection.cursor()
        cur.execute("INSERT INTO users (name, email, phone) VALUES (%s, %s, %s)", (name, email, phone))
        mysql.connection.commit()
        return redirect(url_for('myadmin'))


@app.route('/update',methods=['POST','GET'])
def update():

    if request.method == 'POST':
        id_data = request.form['id']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        cur = mysql.connection.cursor()
        cur.execute("""
               UPDATE users
               SET name=%s, email=%s, phone=%s
               WHERE id=%s
            """, (name, email, phone, id_data))
        flash("Data Updated Successfully", "success")
        mysql.connection.commit()
        return redirect(url_for('myadmin'))

@app.route('/delete/<string:id_data>', methods = ['GET'])
def delete(id_data):
    flash("Record Has Been Deleted Successfully", "success")
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM users WHERE id=%s", (id_data,))
    mysql.connection.commit()
    return redirect(url_for('myadmin'))



if __name__ == '__main__':
	app.secret_key= "@1234567dailywecoding"
	app.run(debug=True)
