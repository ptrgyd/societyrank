from flask import Flask, render_template,request,make_response,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy import desc
from flask_login import LoginManager,UserMixin,login_user,logout_user,current_user,login_required
import random
import math
import os
import urlparse
import psycopg2

urlparse.uses_netloc.append("postgres")
url = urlparse.urlparse(os.environ["DATABASE_URL"])
conn = psycopg2.connect(
 database=url.path[1:],
 user=url.username,
 password=url.password,
 host=url.hostname,
 port=url.port
)

app = Flask(__name__)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/pmg/Documents/societyRank/societyrank.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/societyrank'
app.config['SECRET_KEY'] = 'secret'


db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
# login_manager.login_message = 'Didnt work'

class Person(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    genus = db.Column(db.String(50))
    species = db.Column(db.String(50))
    nickname = db.Column(db.String(50))
    score = db.Column(db.Integer,default=800)
    last_change = db.Column(db.Integer)

class User(UserMixin,db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(50),unique=True)
    pw = db.Column(db.String)
    email = db.Column(db.String(50))
    votes_left = db.Column(db.Integer)

    person_id = db.Column(db.Integer,db.ForeignKey('person.id'),nullable=False)
    person = db.relationship('Person',backref=db.backref('users', lazy=True))

def decrement(votes):
    updated_votes = votes - 1
    return updated_votes

@login_manager.user_loader   # returns User object with given user_id
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/logmein',methods=['POST'])
def logmein():
    username = request.form['username']
    pw = request.form['pw']
    user = User.query.filter_by(username=username).first()

    if not user:
        return redirect(url_for('index'))

    user_pw = user.pw

    if user and user_pw == pw:
        login_user(user)
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/')
def index():
    logged_user = current_user
    # generating list stuff
    if current_user.is_anonymous:
        persons = Person.query.order_by(Person.id).all()
    else:
        persons = Person.query.filter(Person.id != logged_user.person_id).order_by(Person.id).all()

    person1 = random.choice(persons)
    person2 = random.choice(persons)

    def pair_generator(person1,person2): # makes sure person1,2 are not same; if so, generates a new pair and checks again
        if person1.id == person2.id:
            person1 = random.choice(persons)
            person2 = random.choice(persons)
            return pair_generator(person1,person2)
        else:
            return person1,person2

    x,y = pair_generator(person1,person2) # fxn returns tuple of Objects, which are passed into x,y

    return render_template('index.html',persons=persons,x=x,y=y,logged_user=logged_user) # index refresh queries database to reflect new scores


@app.route('/elo/<winner_id>/<winner_score>/<loser_id>/<loser_score>')
@login_required
def elo(winner_id,winner_score,loser_id,loser_score):
    logged_user = current_user
    winner_score = int(winner_score)
    loser_score = int(loser_score)
    winner_id = int(winner_id)
    loser_id = int(loser_id)
    k = 100

    def expected(higher_score,lower_score):
        expected = 1 / (1 + 10**(float(lower_score - higher_score)/400))
        return expected

    # simplified elo
    def score_change(winner_score,loser_score):
        if winner_score >= loser_score:
            e = expected(winner_score,loser_score)
            score_change = k * (1-e)
            score_change = round(score_change)
            return score_change
        else:
            e = expected(loser_score,winner_score)
            score_change = k * (1-(1-e))
            score_change = round(score_change)
            return score_change

    def elo_mod(winner_score,loser_score,score_change):
        updated_winner = winner_score + score_change
        updated_loser = loser_score - score_change
        return updated_winner,updated_loser

    def calc_change(entry_score,updated_score):
        last_change = updated_score - entry_score
        return last_change

    winner_object = Person.query.filter_by(id=winner_id).first()
    loser_object = Person.query.filter_by(id=loser_id).first()

    score_change = score_change(winner_score,loser_score)

    updated_winner_score,updated_loser_score = elo_mod(winner_score,loser_score,score_change)

    winner_object.score = updated_winner_score
    loser_object.score = updated_loser_score

    winner_object.last_change = calc_change(winner_score,updated_winner_score)
    loser_object.last_change = calc_change(loser_score,updated_loser_score)

    current_votes = logged_user.votes_left
    logged_user.votes_left = decrement(current_votes)

    db.session.commit()

    return redirect(url_for('index'))


@app.route('/rankings')
def rankings():
    persons = Person.query.order_by(desc(Person.score)).all()

    return render_template('rankings.html',persons=persons)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8800, debug=True)
