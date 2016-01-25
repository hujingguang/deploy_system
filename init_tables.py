from app import app,db
from app.models import *

#repo_table=''' create table repos_info (id int not null primary key,repo_name char(200) not null ,repo_address varchar(100) not null,repo_user varchar(20) not null,repo_passwd varchar(100) not null,local_checkout_path varchar(100) not null,repo_type char(10) not null,remote_deploy_path varchar(100) not null)'''

def init_db_user():
    db.create_all()

if __name__=="__main__":
    init_db_user()
