#coding=utf-8
from werkzeug import generate_password_hash,check_password_hash
from app import app,db 
from datetime import datetime
class User(db.Model):
    __tablename__ = 'users'
    uid = db.Column(db.Integer, primary_key = True)
    email = db.Column(db.String(120), unique=True)
    passwdhash = db.Column(db.String(200))

    def __init__(self,email,password):
        self.email = email.lower()
        self.set_password(password)
    def is_authenticated(self):
        return True
    def is_active(self):
        return True
    def is_anonymous(self):
        return False
    def get_id(self):
        return unicode(str(self.uid))
    def set_password(self, password):
        self.passwdhash = generate_password_hash(password)             
    def check_password(self, password):
        return check_password_hash(self.passwdhash, password)


''' 
添加版本库表结构
'''
class RepoInfo(db.Model):
    __tablename__='repos_info'
    uid=db.Column(db.Integer,primary_key=True)
    repo_name=db.Column(db.String(120),unique=True)
    repo_address=db.Column(db.String(120))
    repo_user=db.Column(db.String(100))
    repo_passwd=db.Column(db.String(100))
    local_checkout_path=db.Column(db.String(100))
    repo_type=db.Column(db.String(100))
    online_deploy_path=db.Column(db.String(100))
    test_deploy_path=db.Column(db.String(100))
    exclude_dir=db.Column(db.Text)
    def __init__(self,repo_name,repo_address,repo_user,repo_passwd,local_checkout_path,repo_type,online_deploy_path,test_deploy_path,exclude_dir):
        self.repo_name=repo_name
        self.repo_address=repo_address
        self.repo_user=repo_user
        self.local_checkout_path=local_checkout_path
        self.repo_type=repo_type
        self.repo_passwd=repo_passwd
        self.online_deploy_path=online_deploy_path
        self.test_deploy_path=test_deploy_path
        self.exclude_dir=exclude_dir

'''
添加操作记录关系模型
'''

class DeployInfo(db.Model):
    __tablename__='deploy_info'
    id=db.Column(db.Integer,primary_key=True)
    repo_name=db.Column(db.String(100))
    #deploy_repo=db.Column(db.String(100))
    now_version=db.Column(db.String(100))
    #old_version=db.Column(db.String(100))
    deploy_target=db.Column(db.String(100))
    deploy_env=db.Column(db.String(100))
    #repo_type=db.Column(db.String(100))
    deploy_person=db.Column(db.String(50))
    deploy_date=db.Column(db.DateTime(),default=datetime.now)
    #remarks=db.Column(db.String(200))
    update_log=db.Column(db.Text())
    def __init__(self,repo_name,now_version,deploy_target,deploy_env,deploy_person,deploy_date,update_log):
        self.repo_name=repo_name
        #self.deploy_repo=deploy_repo
        self.now_version=now_version
        #self.old_version=old_version
        self.deploy_target=deploy_target
        self.deploy_env=deploy_env
        #self.repo_type=repo_type
        self.deploy_person=deploy_person
        #self.remarks=remarks
        self.update_log=update_log

