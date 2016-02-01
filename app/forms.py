
#-*- coding: utf-8 -*- 
from flask.ext.wtf import Form
from wtforms import StringField,BooleanField,SelectField,TextField,SubmitField,PasswordField,ValidationError
from wtforms.validators import DataRequired,Email,EqualTo,Regexp
from app import db
from models import RepoInfo

class LoginForm(Form):
    email = StringField('Email', validators=[DataRequired("Please enter your email address."),Email("Please enter your email address.")])
    password = PasswordField('Password', validators=[DataRequired("Please enter a password.")])

class ReposForm(Form):
    repo_name=StringField('Repo_Name',validators=[DataRequired("请输入库名")])
    repo_address=StringField('Repo_Address',validators=[DataRequired("请输入版本库地址")])
    repo_user=StringField('Repo_User',validators=[DataRequired("请输入库用户")])
    repo_passwd=PasswordField('Repo_Passwd',validators=[DataRequired("请输入密码")])
    local_checkout_path=StringField('local_checkout_dir',validators=[Regexp('^/.*'),DataRequired("请输入本地checkout目录")])
    online_deploy_path=StringField('Online_Deploy_Url',validators=[DataRequired("请输入正式环境发布绝对路径")])
    test_deploy_path=StringField('Test_Deploy_Url',validators=[DataRequired("请输入测试环境发布绝对路径")])
    repo_type=SelectField('Repo_Type',choices=[('svn','Svn'),('git','Git')])
    exclude_dir=TextField('Exclude_Dir')



def checkall_reponame():
    L=[]
    names=db.session.query(RepoInfo.repo_name)
    for name in names:
        L.append((name[0],name[0]))
    return L



class DeployForm(Form):
    repo_name=QuerySelectField('Repo_Name',query_factory=lambda :RepoInfo.query.order_by('repo_name'),get_label=lambda x:x.repo_name)
    #repo_name=SelectField('Repo_Name',choices=[(obj.repo_name,obj.repo_name) for obj in RepoInfo.query.order_by('repo_name')])
    deploy_env=SelectField('Deploy_Env',choices=[('test','Test'),('online','Online')]) 
    password=PasswordField('Passwd',validators=[DataRequired("Please enter password")])

