from peewee import *

db = SqliteDatabase('games.db')

class Game(Model):
    id = AutoField()
    name = CharField()
    author = CharField()
    year = IntegerField()

    class Meta:
        database = db

db.connect()
db.create_tables([Game])