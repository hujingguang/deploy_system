# deploy_project_system
deploy project system

  这是一个版本发布系统，主要使用了rsync来对svn库和Git库中的代码进行同步

数据库配置在  app/__init__.py文件中 app.config['SQLALCHEMY_DATABASE_URI']='mysql://username:passwd@IP/database_name' 

该系统运行在centos 6.5 和python 2.7版本上，需要安装的Python第三方模块在app/required.sh文件中



