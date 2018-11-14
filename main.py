from flask import Flask, request, redirect, render_template, session, flash
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash
from datetime import datetime
from sqlalchemy import desc
import os

app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:MyBl0gzPass@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'y337kGcys&zP3B'

class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    posts = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), unique=True)
    body = db.Column(db.Text, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    pub_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow())

    def __init__(self, title, body, owner, pub_date):
        self.title = title
        self.body = body
        self.owner = owner
        self.pub_date = pub_date


@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'static', 'index', 'blog']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')


@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user:
            if check_pw_hash(password, user.pw_hash):
                session['username'] = username
                msg = "Welcome back, {0}!".format(username)
                flash(msg, 'info')
                return redirect('/newpost')
            flash('Password for ' + username + ' is incorrect...', 'danger')
        else:
            flash('User "' + username + '" does not exist...', 'danger')

    return render_template('login.html', title="Login | Blogz!")


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        # validate user's data
        if not not_empty(username):
            flash('Please choose a username', 'danger')
            return render_template('signup.html')
        if len(username) < 3:
            flash('Please enter a username of at least 3 characters...', 'danger')
            return render_template('signup.html', username=username, title="Signup | Blogz!")
        if not not_empty(password):
            flash('Please enter a password', 'danger')
            return render_template('signup.html', username=username, title="Signup | Blogz!")
        if len(password) < 3:
            flash('Please enter a password of at least 3 characters...', 'danger')
            return render_template('signup.html', username=username, title="Signup | Blogz!")
        if not not_empty(verify):
            flash('Please re-enter password', 'danger')
            return render_template('signup.html', username=username, title="Signup | Blogz!")
        if password != verify:
            flash('Password and Verify Password fields do not match...', 'danger')
            return render_template('signup.html', username=username, title="Signup | Blogz!")

        # check for existing user in database
        existing_user = User.query.filter_by(username=username).first()
        if not existing_user:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            msg = "Logged in as {0}".format(username)
            flash(msg, 'info')
            return redirect('/newpost')
        else:
            flash("The username <strong>{0}</strong> is already signed up...".format(username), 'danger')

    return render_template('signup.html', title="Signup | Blogz!")


@app.route('/logout', methods=['POST'])
def logout():
    del session['username']
    return redirect('/blog')


@app.route('/', methods=['POST', 'GET'])
def index():

     authors = User.query.order_by('username').all()
     return render_template('index.html', title="Blogz!", authors=authors)

@app.route('/newpost', methods=['POST', 'GET'])
def newpost():

    owner = User.query.filter_by(username=session['username']).first()
    
    if request.method == 'POST':
        post_title = request.form['title']
        post_body = request.form['body']
        pub_date = datetime.utcnow()
        if not not_empty(post_title):
            flash('Please enter a title', 'danger')
            return render_template('newpost.html', post_body=post_body, title="New Post | Blogz!")
        if not not_empty(post_body):
            flash('Please enter some text in the body', 'danger')
            return render_template('newpost.html', post_title=post_title, title="New Post | Blogz!")
        new_post = Blog(post_title, post_body, owner, pub_date)
        db.session.add(new_post)
        db.session.commit()
        id = new_post.id
        url = 'blog?id=' + str(id)
        return redirect(url)
        

    posts = Blog.query.filter_by(owner=owner).all()
    return render_template('newpost.html', title="New Post | Blogz!",
                           posts=posts)
def not_empty(string):
    if string == '':
        return False
    else:
        return True


@app.route('/blog', methods=['GET'])
def blog():
    # owner = User.query.filter_by(username=session['username']).first()
    posts = Blog.query.order_by(desc('pub_date')).all()
    if request.args:
        id = request.args.get('id', type=int)
        user = request.args.get('user', type=int)
        if id:
            post = Blog.query.get(id)
            owner_id = post.owner_id
            author = User.query.get(owner_id)
            title = post.title + ' | Blogz!'
            return render_template('blog.html',title=title, post=post, author=author)
        if user:
            author = User.query.get(user)
            posts = Blog.query.filter_by(owner_id=user).order_by(desc('pub_date')).all()
            title = author.username + ' | Blogz!'
            return render_template('singleUser.html', title=title, posts=posts, author=author)
    
    return render_template('posts.html', title="Posts | Blogz!",
                           posts=posts)


if __name__ == '__main__':
    app.run()