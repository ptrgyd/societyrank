import os

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'yak23477a5manaf4analal7a4s2h3ashab6a55h'
    SQLALCHEMY_DATABASE_URI = 'postgres://uhtlqlfibuxjfk:1190e4d33358058ac87b39216661f88fc8ff512f15a213dee7d11f0e67d3633c@ec2-184-73-202-112.compute-1.amazonaws.com:5432/d1gosfmdivcf2k'
    SQLALCHEMY_TRACK_MODIFICATIONS = True # to suppress warning, i guess?
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'pgayed@gmail.com' # os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = 'yrpxkcyoareshqjt' # os.environ.get('MAIL_PASSWORD')
