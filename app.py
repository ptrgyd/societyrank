from flask import Flask, render_template,request,make_response,redirect,url_for,flash
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy import desc
from flask_login import LoginManager,UserMixin,login_user,logout_user,current_user,login_required
import random
import math
import os

# THIS BLOCK REQUIRED FOR HEROKU
#
# import urllib.parse # required for heroku
# import psycopg2

# urllib.parse.uses_netloc.append("postgres")
# url = urllib.parse.urlparse(os.environ["DATABASE_URL"])
# conn = psycopg2.connect(
#  database=url.path[1:],
#  user=url.username,
#  password=url.password,
#  host=url.hostname,
#  port=url.port
# )

app = Flask(__name__)

# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/societyrank'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/pmg/Documents/societyRank/societyrank.db'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://uhtlqlfibuxjfk:1190e4d33358058ac87b39216661f88fc8ff512f15a213dee7d11f0e67d3633c@ec2-184-73-202-112.compute-1.amazonaws.com:5432/d1gosfmdivcf2k'
app.config['SECRET_KEY'] = 'secret'


db = SQLAlchemy(app)
# db = SQLAlchemy(os.environ["DATABASE_URL"]) # Don't need this, I don't think
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

class Transaction(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    voter_id = db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)
    winner_id = db.Column(db.Integer,db.ForeignKey('person.id'),nullable=False)
    loser_id = db.Column(db.Integer,db.ForeignKey('person.id'),nullable=False)
    winner_score = db.Column(db.Integer)
    loser_score = db.Column(db.Integer)
    score_change = db.Column(db.Integer)

    winner = db.relationship('Person',foreign_keys=[winner_id])
    loser = db.relationship('Person',foreign_keys=[loser_id])
    user = db.relationship('User',foreign_keys=[voter_id])

# GLOBAL VARIABLES and FUNCTIONS

# can't put a query in here (like current_rankings) because then it only
# gets generated on app launch (and not on every refresh, as it should be)

def get_current_rankings():
    current_rankings = Person.query.order_by(desc(Person.score)).all()
    return current_rankings

def decrement(votes):
    updated_votes = votes - 1
    return updated_votes

@login_manager.user_loader   # returns User object with given user_id
def load_user(user_id):
    return User.query.get(int(user_id))

persons = None

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
        logged_user = current_user
        persons_list = Person.query.filter(Person.id != logged_user.person_id).all()
        global persons
        persons = persons_list
        return redirect(url_for('index'))
    else:
        return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/',methods=['GET'])
def index(x=None,y=None):
    logged_user = current_user
    current_rankings = get_current_rankings()

    def pair_generator(person1,person2): # makes sure person1,2 are not same; if so, generates a new pair and checks again
        if person1.id == person2.id:
            person1 = random.choice(persons)
            person2 = random.choice(persons)
            return pair_generator(person1,person2)
        else:
            return person1,person2

    if not logged_user.is_anonymous:

        current_votes = logged_user.votes_left
        logged_user.votes_left = decrement(current_votes)

        db.session.commit()

        # persons = Person.query.filter(Person.id != logged_user.person_id).all()
        person1 = random.choice(persons)
        person2 = random.choice(persons)
        x,y = pair_generator(person1,person2) # fxn returns tuple of Objects, which are passed into x,y

    return render_template('index.html',x=x,y=y,logged_user=logged_user,current_rankings=current_rankings) # index refresh queries database to reflect new scores


@app.route('/ello',methods=['POST'])
@login_required
def ello():

    logged_user = current_user

    if request.method == 'POST':
        winner_id = int(request.form['winner_id'])
        winner_score = int(request.form['winner_score'])
        loser_id = int(request.form['loser_id'])
        loser_score = int(request.form['loser_score'])
    else:
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

    if not loser_id == 6:
        score_change = score_change(winner_score,loser_score)

        updated_winner_score,updated_loser_score = elo_mod(winner_score,loser_score,score_change)

        winner_object.score = updated_winner_score
        loser_object.score = updated_loser_score

        winner_object.last_change = calc_change(winner_score,updated_winner_score)
        loser_object.last_change = calc_change(loser_score,updated_loser_score)

    else:
        # score_change = 99

        winner_object.score = winner_object.score - 9
        loser_object.score = loser_object.score + 99

        winner_object.last_change = -9
        loser_object.last_change = 99


    # create new transaction // must be AFTER score_change is calculated
    new_transaction = Transaction(voter_id=logged_user.id,
                                  winner_id=winner_id,
                                  loser_id=loser_id,
                                  winner_score=winner_score,
                                  loser_score=loser_score,
                                  score_change=winner_object.last_change)
    db.session.add(new_transaction)

    # commit all to database
    db.session.commit()

    return redirect(url_for('index'))


@app.route('/rankings')
def rankings():
    current_rankings = get_current_rankings()

    return render_template('rankings.html',current_rankings=current_rankings)

@app.route('/transactions')
@login_required
def transactions():
    transactions = Transaction.query.all()

    return render_template('transactions.html',transactions=transactions)

@app.route('/about')
def about():

    return render_template('about.html')


if __name__ == '__main__':
    app.run(
    host='0.0.0.0', port=8800, debug=True
    )
