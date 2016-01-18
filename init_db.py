from app import app,db
from app.models import User
def init_db_user():
    user=User('hoo@wikiki.cn','meitianhui')
    db.session.add(user)
    db.session.commit()


if __name__=="__main__":
    init_db_user()
