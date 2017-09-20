from flask import Flask
from wtforms import StringField, SubmitField, PasswordField, validators, TextAreaField, HiddenField
from wtforms.validators import Required
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect


class PostForm(FlaskForm):
        msg = TextAreaField('Post a message',
                            [validators.DataRequired(),
                             validators.Length(max=140, message='max 140 characters')])
        submit = SubmitField('Post')


class CommentForm(FlaskForm):
        comment = TextAreaField('Comment',
                                [validators.DataRequired(),
                                 validators.Length(max=140, message='max 140 characters')])
        hidden_msg_id = HiddenField('msg_id')
        submit = SubmitField('Comment')


class RegisterForm(FlaskForm):
        # inherit from FlaskFrom to make registration form
        fname = StringField('First Name: ',
                            [validators.DataRequired(),
                             validators.Length(min=2, max=25),
                             validators.Regexp('^[a-zA-Z]+$')])
        lname = StringField('Last Name: ',
                            [validators.DataRequired(),
                             validators.Length(min=2, max=25),
                             validators.Regexp('^[a-zA-Z]+$')])
        email = StringField('Email: ',
                            [validators.DataRequired(),
                             validators.Email('Invalid email!')])
        psw = PasswordField('Password: ',
                            [validators.DataRequired(),
                             validators.Length(min=4, max=25),
                             validators.DataRequired(),
                             validators.EqualTo('psw_confirm')])
        psw_confirm = PasswordField('Confirm psw: ', 
                                    [validators.DataRequired()])
        submit = SubmitField('Submit')


class LoginForm(FlaskForm):
        # inherit from FlaskForm to make login form
        email = StringField('Email: ',
                            [validators.DataRequired(),
                            validators.Email('Invalid email')])
        psw = PasswordField('Password: ', [validators.DataRequired()])
        submit = SubmitField('Login')