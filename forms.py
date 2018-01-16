from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,BooleanField,SubmitField,TextAreaField,HiddenField
from wtforms.validators import DataRequired,Length

class LoginForm(FlaskForm):
    username = StringField('username', validators=[DataRequired('enter username, idiot.')])
    password = PasswordField('p@ssw3rd', validators=[DataRequired('enter p@ssw3rd, idiot.')])
    # remember_me = BooleanField('Remember Me')
    submit = SubmitField('log me in bruh')

class CommentBox(FlaskForm):
    comment = TextAreaField('',validators=[DataRequired('You can\'t submit nothing, ya dummy.'),Length(1,280,'Nice try. Keep it under 280 characters.')])
    submit = SubmitField('Submit')

class VoteForm(FlaskForm):
    winner_idd = HiddenField()
    loser_idd = HiddenField()
