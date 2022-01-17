
from app import app
from models import User, Feedback, db

db.drop_all()
db.create_all()

u = User.register("testername", "eggpassword", "Egg", "Eggerton", "egg@gmail.egg")
db.session.add(u)
db.session.commit()