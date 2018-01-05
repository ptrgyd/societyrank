from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,BooleanField,SubmitField,TextAreaField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired()])
    password = PasswordField('p@ssw3rd', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('log me in bruh')

class CommentBox(FlaskForm):
    comment = TextAreaField('',validators=[])
    submit = SubmitField('Submit')
