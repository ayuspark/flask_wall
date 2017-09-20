from flask import Flask, render_template, redirect, request, url_for, flash, session
#general flask import

from flask_wtf.csrf import CSRFProtect
# Exempt hand-built form

from flask_bootstrap import Bootstrap
# Use bootstrap to create quickform

import md5
import os
import binascii
# Mask password

from mysqlconnection import MySQLConnector, MySQLConnection
# Connect to my own database

from forms import LoginForm, RegisterForm, PostForm
# Create forms using my own module


app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard to guess string'

csrf = CSRFProtect(app)
csrf.init_app(app)

bootstrap = Bootstrap(app)
mysql = MySQLConnection(app, 'walls_db')


@app.route('/', methods=['GET', 'POST'])
def index():
        msg_form = PostForm()
        if 'name' not in session:
                session['name'] = ''
        # Display all messages
        query = """SELECT CONCAT_WS(' ', users.fname, users.lname) AS name,
                messages.msg, 
                DATE_FORMAT(messages.created_at, \"%M %D %Y %T\") AS created_at, 
                messages.id AS msg_id, 
                users.id AS user_id
                FROM messages
                JOIN users ON messages.user_id = users.id
                ORDER BY messages.created_at DESC
                """
        post_results = mysql.query_db(query)

        query = """SELECT CONCAT_WS(' ', users.fname, users.lname) AS name, 
                comments.comment AS comment, 
                DATE_FORMAT(comments.created_at, \"%M %D %Y %T\") AS created_at, 
                comments.id, users.id AS user_id, 
                comments.message_id 
                FROM comments JOIN messages 
                ON comments.message_id = messages.id 
                JOIN users ON comments.user_id = users.id ORDER BY comments.created_at ASC
                """
        comment_results = mysql.query_db(query)
        
        return render_template('index.html',
                               msg_form=msg_form,
                               post_results=post_results,
                               comment_results=comment_results,
                               name=session['name'])

@app.route('/post', methods=['POST'])
def post_msg():
        msg_form = PostForm()
        if 'user_id' in session:
                if msg_form.validate_on_submit():
                        query = "INSERT INTO messages (msg, user_id, created_at, updated_at) VALUE(:form_msg, :session_user_id, NOW(), NOW())"
                        data = {
                                'form_msg': msg_form.msg.data,
                                'session_user_id': session['user_id'],
                                }
                        mysql.query_db(query, data)
                        return redirect(url_for('index'))
        else:
                flash('Please register or log in!')
        return redirect(url_for('index'))


@app.route('/comment', methods=['POST'])
@csrf.exempt
def post_comment():
        if 'email' not in session or session['email'] == '':
                flash('Please log in or register first!')
        else:
                if request.method == 'POST':
                        query = "INSERT INTO comments (comment, user_id, message_id, created_at, updated_at) VALUE(:form_comment, :session_user_id, :current_msg_id, NOW(), NOW())"
                        data = {
                                'form_comment': request.form['comment'],
                                'session_user_id': session['user_id'],
                                'current_msg_id': request.form['msg_id_for_comment'],
                                }
                        mysql.query_db(query, data)
                        # print(mysql.query_db(query, data))
        return redirect(url_for('index'))

        

@app.route('/delete', methods=['POST', 'GET'])
@csrf.exempt
def delete_msg():
        if 'email' not in session or session['email'] == '':
                flash('Please log in or register first!')
        else:
                if request.method == 'POST':
                        if str(session['user_id']) == request.form['user_id']:
                                msg_id_to_delete = request.form['msg_id']
                                data = {
                                        'msg_id': msg_id_to_delete
                                        }
                                # delete comments first, to release foreign_key constraints
                                query = "DELETE FROM comments WHERE message_id=:msg_id"
                                mysql.query_db(query, data)
                                # then delete messages
                                query = "DELETE FROM messages WHERE id=:msg_id"
                                mysql.query_db(query, data)
                                flash('Post deleted!')
                        else:
                                flash('You can only delete your own posts!')
        return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
        form = RegisterForm()
        if 'email' not in session:
                session['email'] = ''
                session['user_id'] = 0
                session['name'] = ''
        if form.validate_on_submit():
                query = "SELECT * FROM users WHERE email=:form_email"
                data = {
                        'form_email': form.email.data,
                        }
                result = mysql.query_db(query, data)
                if result:
                        flash('You have an account, please log in')
                else:
                        form_pwd = form.psw.data
                        salt = binascii.b2a_hex(os.urandom(15))
                        hashed_pwd = md5.new(form_pwd + salt).hexdigest()
                        query = """
                                INSERT INTO users
                                (fname, lname, email, psw, salt, created_at, updated_at)
                                VALUES(:fname, :lname, :email, :psw, :salt, NOW(), NOW())
                                """
                        data = {
                                'fname': form.fname.data,
                                'lname': form.lname.data,
                                'email': form.email.data,
                                'psw': hashed_pwd,
                                'salt': salt,
                                }
                        mysql.query_db(query, data)
                        flash('Success!')
                # automatic log in after registration
                query = "SELECT id FROM users WHERE email=:form_email"
                data = {
                        'form_email': form.email.data,
                        }
                result = mysql.query_db(query, data)
                session['email'] = form.email.data
                session['user_id'] = result[0]['id']
                session['name'] = form.fname.data
                return redirect(url_for('index'))
        return render_template('register.html', form=form)


@app.route('/login', methods=['POST', 'GET'])
def login():
        form = LoginForm()
        if form.validate_on_submit():
                query = "SELECT * FROM users WHERE email=:form_email"
                data = {
                        'form_email': form.email.data
                        }
                result = mysql.query_db(query, data)
                # print(result)
                if result:
                        form_pwd = form.psw.data
                        salt = result[0]['salt']
                        hashed_pwd = md5.new(form_pwd + salt).hexdigest()
                        if result[0]['psw'] == hashed_pwd:
                                session['email'] = form.email.data
                                session['user_id'] = result[0]['id']
                                session['name'] = result[0]['fname'].title()
                                # print(session['email'])
                                # print('email: ', result[0]['email'])
                                flash('Success!')
                        else:
                                flash('Somgthing is fishy...')
                else:
                        flash("Your account doesn't exist!")
        if 'email' not in session:
                session['email'] = ''
                session['user_id'] = 0
        elif session['email'] != '':
                # print('session: ', session['email'])
                flash('You are logged in! Your email is: %s' % (session['email']))
        return render_template('login.html', form=form)


app.run(debug=True)

