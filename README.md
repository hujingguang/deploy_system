# deploy_project_system
deploy project system

  这是一个版本发布系统，主要使用了rsync来对svn库和Git库中的代码进行同步

数据库配置在  app/__init__.py文件中 app.config['SQLALCHEMY_DATABASE_URI']='mysql://username:passwd@IP/database_name' 

该系统运行在centos 6.5 和python 2.7版本上，需要安装的Python第三方模块在app/required.sh文件中

运行该系统需初始化数据库表

init_tables.py 文件包括两个方法：
 
 1 init_db_user()  用来创建数据库表以及初始化一个账号，该账号用户名为邮箱格式，否则报错，
 2 insert



