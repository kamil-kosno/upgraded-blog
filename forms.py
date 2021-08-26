from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, HiddenField
from wtforms.validators import DataRequired, URL, email
from flask_ckeditor import CKEditorField


class PostForm(FlaskForm):
    blog_id = HiddenField(label="Blog ID")
    title = StringField(label="Blog Post Title", validators=[DataRequired()])
    subtitle = StringField(label="Subtitle", validators=[DataRequired()])
    name = StringField(label="Your Name", validators=[DataRequired()], render_kw={'readonly': True})
    img_url = StringField(label="Blog Image URL", validators=[DataRequired(), URL()])
    content = CKEditorField(label="Blog Content", validators=[DataRequired()])
    submit = SubmitField(label="Submit Post")


class RegisterForm(FlaskForm):
    name = StringField(label="Name", validators=[DataRequired()])
    email = StringField(label="Email", validators=[DataRequired(), email()],
                        render_kw={'onclick': "hide('user-duplicate-warn')"})
    password = PasswordField(label="Password", validators=[DataRequired()])
    submit = SubmitField(label="Register")


class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), email()],
                        render_kw={'onclick': "hide('flashes')"})
    password = PasswordField(label="Password", validators=[DataRequired()],
                             render_kw={'onclick': "hide('flashes')"})
    submit = SubmitField(label="Log In")


class CommentForm(FlaskForm):
    comment = CKEditorField(label="Your Comment", validators=[DataRequired()])
    submit = SubmitField(label="Submit")
