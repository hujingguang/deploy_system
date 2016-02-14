# deploy_project_system
deploy project system

  这是一个版本发布系统，主要使用了rsync来对svn库和Git库中的代码进行同步

数据库配置在  app/__init__.py文件中 app.config['SQLALCHEMY_DATABASE_URI']='mysql://username:passwd@IP/database_name' 

该系统运行在centos 6.5 和python 2.7版本上，需要安装的Python第三方模块在app/required.sh文件中

运行该系统需初始化数据库表

init_tables.py 文件包括两个方法：
 
 1     init_db_user()  用来创建数据库表以及初始化一个账号，该账号用户名必须为邮箱格式，否则报错.

 2     insert_first_sql_for_deploy() 用来插入第一条代码发布日志，系统根据此记录确定上次发布版本号.  
 该方法的三个参数依次为： 
 
 repoName  库名，在系统中添加成功的版本库名
 
 now_version 版本号，版本库和发布环境代码完全一致时的版本库版本号，Git为commit id,长度需大于12位
 
 envType    发布环境，选项为 'test'  or   'online'
 
 以上三个参数均需手动添加 并插入！！！
 
 3     根据所添加的库名修改 init_tables.py文件对数据库进行初始化 执行命令 python init_tables.py即可
 
 4     修改run.py 文件绑定当前主机IP及端口,然后运行 python run.py 即可


![](https://github.com/hujingguang/deploy_system/blob/master/screenshots/1.png)
