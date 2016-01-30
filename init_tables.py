#!/usr/bin/python
#-*- coding: utf-8 -*-
from app import app,db
from app.models import *
from datetime import datetime

#repo_table=''' create table repos_info (id int not null primary key,repo_name char(200) not null ,repo_address varchar(100) not null,repo_user varchar(20) not null,repo_passwd varchar(100) not null,local_checkout_path varchar(100) not null,repo_type char(10) not null,remote_deploy_path varchar(100) not null)'''

def init_db_user():
    db.create_all()

def insert_first_sql_for_deploy(repoName,now_version,envtype):
    repo_info=RepoInfo.query.filter_by(repo_name=repoName).first()
    if repo_info:
        if envtype.strip(' ')=='test' or envtype.strip(' ')=='online':
            deploy_info=DeployInfo(repo_info.repo_name,now_version,repo_info.test_deploy_path,envtype.strip(' '),'admin',datetime.now(),'')
            db.session.add(deploy_info)
            try:
                db.session.commit()
            except:
                print '插入数据失败！！！'
                return False
            print '初始化库 %s 发布数据成功！！  ' %repoName
            return True
        else:
            print '请输入正确的环境类型!  测试环境选项: test, 正式环境选项: online'
            return False
    print '初始化失败！不存在库: %s' %repoName

if __name__=="__main__":
    #init_db_user()
    insert_first_sql_for_deploy('Git','3aeb6e21ca06fc4','test')
    insert_first_sql_for_deploy('Git','3aeb6e21ca06fc4','online')



