import os
from sqlalchemy import exc
from flask import Flask, render_template, request, redirect, url_for, flash
from forms import PostForm, RegisterForm, LoginForm, CommentForm
from flask_bootstrap import Bootstrap
from emailmanager import send_email
from flask_sqlalchemy import SQLAlchemy
from flask_ckeditor import CKEditor
from datetime import datetime
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from passmanager import PasswordManager
from werkzeug.security import check_password_hash
from functools import wraps
import hashlib
import setup

# postgres://vszkiqjapbagzv:e06387cbbf6e7b8024b013fe1df2f7e516d485b59d84b4e8870eed5874e24907@ec2-54-156-151-232.compute-1.amazonaws.com:5432/dchm92j6sq4uvl

GRAVATAR_API_URL = "https://www.gravatar.com/avatar/"
DB_NAME = 'blog.db'
login_manager = LoginManager()
app = Flask(__name__)
Bootstrap(app)
ckeditor = CKEditor(app)

##Connect to Database
DB_URL = os.getenv('DATABASE_URL')
if DB_URL.startswith('postgres://'):
    DB_URL = DB_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("APP_SECRET_KEY")
login_manager.init_app(app)
db = SQLAlchemy(app)


class Post(db.Model):
    __tablename__ = 'blog_posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(1000), nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref="post", lazy=True)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('blog_posts.id'), nullable=False)
    text = db.Column(db.String(1000), nullable=False)


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    posts = db.relationship('Post', backref='user', lazy=True)
    # one-to-one relation: uselist=False
    admin = db.relationship('Admin', lazy=True, uselist=False)
    comments = db.relationship('Comment', lazy=True, backref="user")

    def get_email_hash(self):
        email_str = (self.email.strip()).encode("utf-8")
        email_hash = hashlib.md5(email_str).hexdigest()
        return f"{GRAVATAR_API_URL}{email_hash}"


class Admin(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    isadmin = db.Column(db.Integer)


# Line below only required once, when creating DB.
db.create_all()


def get_posts(blog_id=None):
    if blog_id is None:
        result = Post.query.all()
    else:
        result = Post.query.get(blog_id)
    return result


# return current user
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


def is_admin():
    try:
        if int(current_user.admin.isadmin) == 1:
            return True
    except AttributeError:
        return False
    return False


def admin_only(func):
    @wraps(func)
    def decorated_function(*args, **kwargs):
        if not is_admin():
            return "Access denied", 403
        return func(*args, **kwargs)
    return decorated_function


@app.route('/')
def home():
    return render_template('index.html', posts=get_posts(), is_admin=is_admin())


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST':
        check = User.query.filter_by(email=form.email.data).first()
        if not check:
            if form.validate_on_submit():
                new_user = User(
                    email=form.email.data,
                    password=PasswordManager.get_hash(form.password.data),
                    name=form.name.data
                )
                db.session.add(new_user)
                db.session.commit()
                return redirect(url_for('login'))
        else:
            flash("You've already registered with this email. Log in instead.")
            return redirect(url_for('login'))
    return render_template("register.html", form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            user = User.query.filter_by(email=email).first()
            if not user:
                flash(f'User with email {email} does not exist. Please try again.')
                return render_template("login.html", form=form)
            elif check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('The password is incorrect. Please try again.')
                return render_template("login.html", form=form)
    return render_template("login.html", form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/delete/<post_id>')
@admin_only
def delete(post_id):
    post = get_posts(post_id)
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/new-post', methods=['GET', 'POST'])
@admin_only
def new_post():
    form = PostForm()
    form.name.data = current_user.name
    if request.method == 'POST':
        if form.validate_on_submit():
            if form.blog_id.data:
                print('this is wrong')
                post = get_posts(blog_id=int(form.blog_id.data))
                post.title = form.title.data
                post.body = form.content.data
                post.author_id = current_user.id
                post.img_url = form.img_url.data
                post.subtitle = form.subtitle.data
                db.session.commit()
            else:
                current_date = datetime.now().date()
                current_date = datetime.strftime(current_date, f'%B {current_date.day}, %Y')
                post = Post(
                    title=form.title.data,
                    body=form.content.data,
                    author_id=current_user.id,
                    img_url=form.img_url.data,
                    subtitle=form.subtitle.data,
                    date=current_date
                )
                db.session.add(post)
                db.session.commit()
            return redirect(url_for('home'))
        else:
            for field in form:
                if field.errors:
                    field.render_kw = {'autofocus': True}
                    break
    # GET
    else:
        if 'blog_id' in request.args:
            blog_id = request.args['blog_id']
            blog_post = get_posts(blog_id=blog_id)
            form.blog_id.data = blog_id
            form.title.data = blog_post.title
            form.name.data = blog_post.user.name
            form.subtitle.data = blog_post.subtitle
            form.content.data = blog_post.body
            form.img_url.data = blog_post.img_url
    return render_template('make-post.html', form=form)


@app.route('/post/<int:blog_id>', methods=['GET', 'POST'])
def blogpost(blog_id):
    form = CommentForm()
    blog_post = get_posts(blog_id=blog_id)
    if request.method == 'POST':
        if form.validate_on_submit():
            new_comment = Comment(
                author_id=current_user.id,
                text=form.comment.data,
                post_id=blog_id
            )
            db.session.add(new_comment)
            db.session.commit()
            form.comment.data = ""
    return render_template("post.html", blog_post=blog_post, form=form, is_admin=is_admin())


@app.route('/edit-post/<int:blog_id>')
@admin_only
def edit_post(blog_id):
    return redirect(url_for('new_post', blog_id=blog_id))


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    smtp_server = os.getenv('SMTP_SERVER')
    user = os.getenv('EMAIL_APP_USER')
    if request.method == 'GET':
        page_header = 'Contact Me'
    else:
        send_email(request.form)
        page_header = 'Successfully sent your message'
    return render_template('contact.html', page_header=page_header, smtp_server=smtp_server, user=user)


if __name__ == "__main__":
    app.run(debug=True)
