#!/usr/bin/python
#-*- coding: utf-8 -*- 
from flask import Flask,render_template,request,session,flash,redirect,url_for,g,Blueprint
#from flask import *
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager,login_user,logout_user,current_user,login_required
from app import app,db,lm
from app.models import User,RepoInfo,DeployInfo
from flask.ext.paginate import Pagination
from sqlalchemy import desc
import os,commands,time,pexpect,re
from datetime import datetime
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
Log_File='/tmp/deploy.log'      #程序运行的日志文件
Update_File='/tmp/update.log'   #记录更新文件的日志文件
Backup_Dir='/home/backup'       #正式环境备份目录
TIMEFORMAT='%Y-%m-%d %X'
mod=Blueprint('views',__name__)
bootstrap=Bootstrap(app)



@lm.user_loader
def load_user(uid):
    return User.query.get(int(uid))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login')) 


@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('home.html')

@app.route('/add/repos',methods=['GET','POST'])
@login_required
def add_repos():
    from forms import ReposForm
    form=ReposForm()
    #if request.method=='GET':
    #    return render_template('add-repo.html',form=form)
    if form.validate_on_submit():
        repo=RepoInfo.query.filter_by(repo_name=form.repo_name.data).first()
        if repo is not None:
            form.repo_name.errors.append("库名已存在!!!!")
            return render_template('add-repo.html',form=form)
        type_info=form.repo_type.data.encode('utf-8').strip(' ')
        if type_info == 'svn':
            check_is_error,info=check_svn_validated(form.repo_user.data,form.repo_passwd.data,form.repo_address.data)
            if not check_is_error:
                return render_template('add-repo.html',form=form,ErrorInfo=info)
        if type_info == 'git':
            check_is_error,info=check_git_validated(form.repo_address.data.encode('utf-8').strip(' '))
            if not check_is_error:
                return render_template('add-repo.html',form=form,ErrorInfo=info)
        repo=RepoInfo(form.repo_name.data,form.repo_address.data,form.repo_user.data,form.repo_passwd.data,form.local_checkout_path.data,form.repo_type.data,form.online_deploy_path.data,form.test_deploy_path.data,form.exclude_dir.data)
        db.session.add(repo)
        db.session.commit()
        return redirect(url_for('display_repos_info')) 
    return render_template('add-repo.html',form=form)






@app.route('/list/repoinfo')
@login_required
def display_repos_info():
    counts=db.session.query(db.func.count('*')).select_from(RepoInfo).scalar()
    per_page=5
    search=False
    q=request.args.get('q')
    if q:
        search=True
    try:
        page=int(request.args.get('page',1))
    except ValueError:
        page=1
    offset=(page-1)*per_page
    sql='select * from repos_info limit {},{}'.format(offset,per_page)
    repos=db.session.query(RepoInfo).from_statement(db.text(sql)).all()
    pagination = Pagination(page=page,link_size='sm',total=counts, record_name='repos',per_page=per_page,bs_version=3,format_total=True,format_number=True,show_single_page=False)
    return render_template('list-repo.html',repos=repos,pagination=pagination,page=page,per_page=per_page)


@app.route('/list/repoinfo/search',methods=['GET','POST'])
@login_required
def search_repos_info():
    if request.method=='POST' and request.form.get('repo',None) :
        args='%'+request.form.get('repo').encode('utf-8')+'%'
        repos=db.session.query(RepoInfo).filter(RepoInfo.repo_name.like(args))
        return render_template('repo-search.html',repos=repos)
    return redirect(url_for('display_repos_info'))



@app.route('/deploy',methods=['GET','POST'])
@login_required
def deploy_project():
    from forms import DeployForm
    form=DeployForm()
    auth=False
    #res=RepoInfo.query()
    if form.validate_on_submit():
        if check_deploy_passwd(form.repo_name.data.repo_name,form.deploy_env.data,form.password.data):
            #开始发布代码
            #repo_type=RepoInfo.query.filter_by(repo_name=form.repo_name.data).first().repo_type.encode('utf-8')
            result,info=get_deploy_info(form.repo_name.data.repo_name.encode('utf-8').strip(' '),form.deploy_env.data.encode('utf-8').strip(' '),form.password.data.encode('utf-8').strip(' '),g.user.email.encode('utf-8').strip(' '))
            if result:
                return redirect(url_for('display_deploy_info'))
            else:
                return render_template('deploy.html',form=form,errors=info)
        else:
            auth=True
            return render_template('deploy.html',auth=auth,form=form)
    return render_template('deploy.html',form=form,auth=auth)




@app.route('/list/deployinfo/search',methods=['GET','POST'])
@login_required
def search_deploy_info():
    if request.method=='POST'  and request.form.get('envtype',None) :
        args='%'+request.form.get('repo').encode('utf-8')+'%'
        sql='select * from deploy_info where repo_name like "%'+request.form.get('repo').encode('utf-8')+'%" and deploy_env="'+request.form.get('envtype')+'" order by deploy_info.deploy_date desc'
        deploy=db.session.query(DeployInfo).from_statement(db.text(sql)).all()
        return render_template('deploy-search.html',deploys=deploy)
    return redirect(url_for('display_deploy_info'))




@app.route('/list/deployinfo')
@login_required
def display_deploy_info():
    counts=db.session.query(db.func.count('*')).select_from(DeployInfo).scalar()
    print counts
    per_page=10
    search=False
    q=request.args.get('q')
    if q:
        search=True
    try:
        page=int(request.args.get('page',1))
    except ValueError:
        page=1
    offset=(page-1)*per_page
    sql='select * from deploy_info order by deploy_info.deploy_date desc limit {},{}'.format(offset,per_page)
    deploy=db.session.query(DeployInfo).from_statement(db.text(sql)).all()
    pagination = Pagination(page=page,link_size='sm',total=counts, record_name='deploy',per_page=per_page,bs_version=3,format_total=True,format_number=True,show_single_page=False)
    return render_template('list-deploy-log.html',deploy=deploy,pagination=pagination,page=page,per_page=per_page)
    


@app.route('/login',methods=['GET','POST'])
def login():
    if g.user is not None and g.user.is_authenticated:
        return redirect(url_for('index'))
    from forms import LoginForm
    form=LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower()).first()
        if user and user.check_password(form.password.data):
            session['email']=form.email.data
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html',form=form,failed_auth=True)
    return render_template('login.html',form=form)

@app.route('/project/backup',methods=['GET','POST'])
@login_required
def backup_or_rollback():
    from forms import BackupForm
    form=BackupForm()
    if form.validate_on_submit():
        repoName=form.repo_name.data.repo_name.encode('utf-8').strip(' ')
        envType='online'
        passwd=form.password.data.encode('utf-8')
        types=form.back_or_roll.data.encode('utf-8').strip(' ')
        exclude_dir=form.exclude_dir.data.encode('utf-8').strip(' ')
        if check_deploy_passwd(repoName,envType,passwd):
            result,info=backup_rollback_online(repoName,exclude_dir,passwd,types)
            if result:
                return render_template('backup.html',form=form,info=info)
            else:
                return render_template('backup.html',form=form,errors=info)
        return render_template('backup.html',form=form,auth=True) 
    return render_template('backup.html',form=form)

    

def backup_rollback_online(repoName,exclude_dir,passwd,types):
    global Backup_Dir
    repo=RepoInfo.query.filter_by(repo_name=repoName).first()
    if repo is None:
        return False,u'获取库信息失败,请检查数据库是否有该库记录'
    deploy_target=repo.online_deploy_path.encode('utf-8').strip(' ')
    exclude_args=deal_with_exclude(exclude_dir)
    if not Backup_Dir.startswith('/'):
        logfunc('Backup_Dir 不合法:     %s' %Backup_Dir)
        return False,u'请配置正确的备份目录'
    if Backup_Dir.endswith('/'):
        num=Backup_Dir.rfind('/')
        Backup_Dir=Backup_Dir[:num]
    local_dir=Backup_Dir+'/'+repoName+'/online_backup'
    if not os.path.exists(local_dir):
        os.system('mkdir -p %s' %local_dir)
    if types=='backup':
        return backup_func(local_dir,deploy_target,passwd,exclude_args)
    else:
        return rollback_func(local_dir,deploy_target,passwd,exclude_args)


def backup_func(local_dir,target_path,passwd,exclude_args):
    if not target_path.endswith('/'):
        target_path=target_path+'/'
    cmd='''rsync -avlP --delete %s %s %s ''' %(exclude_args,target_path,local_dir)
    logfunc('备份命令--------'+cmd)
    if auto_execute_cmd(cmd,passwd):
        return True,u'备份成功！！'
    return False,u'备份失败！！'


def rollback_func(local_dir,target_path,passwd,exclude_args):
    if not local_dir.endswith('/'):
        local_dir=local_dir+'/'
    cmd=''' rsync -avlP %s %s %s ''' %(exclude_args,local_dir,target_path)
    logfunc('还原命令-----------'+cmd)
    if auto_execute_cmd(cmd,passwd):
        return True,u'还原成功'
    return False,u'还原失败'


def auto_execute_cmd(cmd,passwd):
    f=open('/tmp/.backup.sh','w')
    f.write(cmd)
    f.close()
    ch=pexpect.spawn('bash /tmp/.backup.sh')
    res=ch.expect(['yes','assword',pexpect.EOF,pexpect.TIMEOUT],timeout=10)
    if res == 0:
        ch.sendline('yes')
        res=ch.expect(['assword',pexpect.EOF,pexpect.TIMEOUT],timeout=10)
        ch.sendline(passwd)
        loopfunc(ch.pid)
        ch.close(force=True)
    elif res == 1:
        ch.sendline(passwd)
        loopfunc(ch.pid)
        ch.close(force=True)
    else:
        return False
    return True






'''
处理排除目录参数函数
'''    

def deal_with_exclude(exclude_dir):
    exclude_list=exclude_dir.strip(' ').split(';')
    exclude_args=' '
    while '' in exclude_list:
        exclude_list.remove('')
    if len(exclude_list) == 0:
        exclude_args=' '
    elif len(exclude_list) == 1:
        exclude_args=''' --exclude "%s" ''' %exclude_list[0].strip(' ')
    else:
        exclude_files=''
        L=[]
        for f in exclude_list:
            f='"'+f.strip(' ')+'",'
            L.append(f)
        for j in L:
            exclude_files=exclude_files+j
        n=exclude_files.rfind(',')
        exclude_files=exclude_files[:n]
        exclude_args=' --exclude={' +exclude_files+'} '
    return exclude_args

'''
获取发布代码所需信息
'''

def get_deploy_info(repoName,envType,deploy_passwd,deploy_person):
    #repo=db.session.query(RepoInfo).filter(RepoInfo.repo_name=repoName)
    repo=RepoInfo.query.filter_by(repo_name=repoName).first()
    last_deploy=DeployInfo.query.filter_by(repo_name=repoName).filter_by(deploy_env=envType.lower()).order_by(DeployInfo.id.desc()).first()
    if repo is  None or last_deploy is None:
        return False,u'获取发布信息失败'
    types=repo.repo_type.encode('utf-8').strip(' ')
    repo_name=repo.repo_name.encode('utf-8').strip(' ')
    repo_address=repo.repo_address.encode('utf-8').strip(' ')
    repo_user=repo.repo_user.encode('utf-8').strip(' ')
    repo_passwd=repo.repo_passwd.encode('utf-8').strip(' ')
    local_checkout_path=repo.local_checkout_path.encode('utf-8').strip(' ')
    exclude_dir=repo.exclude_dir.encode('utf-8').strip(' ')
    repo_type=repo.repo_type.encode('utf-8').strip(' ').lower()
    if envType=='test':
        deploy_target=repo.test_deploy_path.encode('utf-8').strip(' ')
    else:
        deploy_target=repo.online_deploy_path.encode('utf-8').strip(' ')
    #last_deploy=db.session.query(DeployInfo).filter(DeployInfo.repo_name=repoName).filter(DeployInfo.deploy_env=envType).order_by(Deploy_info.id.desc()).first()
    now_version=last_deploy.now_version.encode('utf-8').strip(' ')
    #print '*************************'
    #print  types,repo_name,repo_address,repo_user,repo_passwd,local_checkout_path,exclude_dir,deploy_target,now_version
    #print '*********************************'
    #res,info=svn_deploy(repoName,local_checkout_path,repo_user,repo_passwd,repo_address,deploy_target,exclude_dir,envType,now_version,deploy_passwd,deploy_person)
    if repo_type =='svn':
        return svn_deploy(repoName,local_checkout_path,repo_user,repo_passwd,repo_address,deploy_target,exclude_dir,envType,now_version,deploy_passwd,deploy_person)
    else:
        return git_deploy(repoName,local_checkout_path,repo_address,deploy_target,exclude_dir,envType,now_version,deploy_passwd,deploy_person)
       


'''
验证发布环境密码正确性
'''
def check_deploy_passwd(repoName,envType,passwd):
    repo=RepoInfo.query.filter_by(repo_name=repoName).first()
    #repo=db.session.query(RepoInfo).filter(RepoInfo.repo_name=repoName).first()
    REX=r'(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[0-9]{1,2})(\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[0-9]{1,2})){3}'
    deploy_path=''
    if repo is not None:
        if envType=='test':
            deploy_path=repo.test_deploy_path.encode('utf-8')
        else:
            deploy_path=repo.online_deploy_path.encode('utf-8')
        if re.search(REX,deploy_path) is None:
            return False
        ip=re.search(REX,deploy_path).group()
        return check_ssh_passwd(passwd,ip)
    return False






'''
实现验证密码功能函数
'''
def check_ssh_passwd(passwd,ip):
    ch=pexpect.spawn('ssh root@%s' %ip)
    res=ch.expect(['yes','assword',pexpect.EOF,pexpect.TIMEOUT],timeout=120)
    if res == 0:
        ch.sendline('yes')
        rs=ch.expect(['assword',pexpect.EOF,pexpect.TIMEOUT],timeout=120)
        ch.sendline(passwd)
        rsz=ch.expect(['assword','#',pexpect.EOF,pexpect.TIMEOUT],timeout=120)
        if rsz == 0:
            ch.close(force=True)
        if rsz == 1:
            ch.close(force=True)
            return True
    if res == 1:
        ch.sendline(passwd)
        rsz=ch.expect(['assword','#',pexpect.EOF,pexpect.TIMEOUT],timeout=120)
        if rsz == 0:
            ch.close(force=True)
        if rsz == 1:
            ch.close(force=True)
            return True
    return False


'''
检查svn地址有效性
'''
def check_svn_validated(user,password,url):
    svn_cmd=''' svn info --non-interactive  --username="%s" --password="%s" %s &>/tmp/.svn_32197''' %(user,password,url)
    print svn_cmd
    result=os.system(svn_cmd)
    if result==0:
        return True,u'ok'
    res=os.system('grep URL /tmp/.svn_32197')
    if res==0:
        return False,u'无效的svn URL地址'
    res=os.system('grep Password /tmp/.svn_32197')
    if res==0:
        return False,u'错误的svn用户密码'
    res=os.system('grep "timed out" /tmp/.svn_32197')
    if res==0:
        return False,u'检车URL超时,请确认地址是否有效！'
    res=os.system('grep "refused" /tmp/.svn_32197')
    if res==0:
        return False,u'拒绝连接该svn地址！'
    res=os.system('grep "Username" /tmp/.svn_32197')
    if res==0:
        return False,u'无效的用户名'
    res=os.system('grep "Unknown hostname" /tmp/.svn_32197')
    if res==0:
        return False,u'错误的svn地址'

'''
检测Git远程库地址是否有效,只适用配置秘钥访问的情况
'''

def check_git_validated(url):
    REX=r'(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[0-9]{1,2})(\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[0-9]{1,2})){3}'
    if not re.search(REX,url):
        return False,u'无效的IP地址 ！！'
    ip=re.search(REX,url).group()
    ch=pexpect.spawn('ssh root@%s' %ip)
    res=ch.expect(['yes',pexpect.EOF,pexpect.TIMEOUT],timeout=4)
    if res==0:
        ch.sendline('yes')
    cmd=r'git clone %s' %url
    ch=pexpect.spawn(cmd)
    res=ch.expect(['done','fatal',pexpect.EOF,pexpect.TIMEOUT],timeout=8)
    if res == 0:
        return True,u'ok'
    elif res == 1:
        return False,u'Git地址不正确或无效,示例: git@192.168.16.23:repo_name'
    else:
        return False,u'检测库地址超时,请确认IP是否正确,且需配置秘钥连接'

    

'''
Git代码发布方法
'''

def git_deploy(repoName,checkDir,repo_address,deploy_target,exclude_dir,envType,now_version,deploy_passwd,deploy_person):
    code_dir=''
    if not checkDir.startswith('/'):
        checkDir="/"+checkDir
    if checkDir.endswith('/'):
        num=checkDir.rfind('/')
        checkDir=checkDir[:num]
    if repo_address.endswith('/'):
        num=repo_address.rfind('/')
        repo_address=repo_address[:num]
    num=repo_address.rfind(':')
    code_dir=repo_address[num+1:]
    local_repo_dir=checkDir+"/"+repoName+'_'+envType
    if not os.path.exists(local_repo_dir):
        os.system('mkdir -p %s' %local_repo_dir)
    if not os.path.exists(local_repo_dir+'/'+code_dir+'/.git'):
        res=os.system(r'cd %s && git clone %s ' %(local_repo_dir,repo_address))
        if res !=0:
            logfunc('Git ----- 克隆远程库失败!!! %s' %repo_address)
            return False,u'初始化代码库失败'
        logfunc('Git----- init git repo Success ')
    res=os.system('cd %s/%s && git pull origin master' %(local_repo_dir,code_dir))
    if res == 0:
        logfunc('Git --- Pull code success')
    else:
        return False,u'获取远程代码失败!!'
    if not os.path.exists('%s/%s/.git/refs/heads/master' %(local_repo_dir,code_dir)):
        logfunc('Git: ERROR   无法获取最新master uid ')
        return False,u'无法获取到最新版本号'
    cmd,last_version=commands.getstatusoutput('cat %s/%s/.git/refs/heads/master' %(local_repo_dir,code_dir))
    last_version=last_version[:12].strip(' ')
    if len(now_version) > 12:
        now_version=now_version[:12].strip(' ')
    if len(now_version) <12:
        return False,u'Git 版本id必须大于12位！！ 请重新初始化'
    if last_version == now_version:
        return False,u'没有代码可更新'
    if now_version.strip(' ') == '':
        return False,u'当前版本为空！！'
    get_diff_cmd=''' cd %s/%s && git diff --name-status  %s %s |sed 's/^[ ]*//g' >/tmp/.git909081''' %(local_repo_dir,code_dir,last_version,now_version)
    logfunc('Git ---- %s' %get_diff_cmd)
    res=os.system(get_diff_cmd)
    if res != 0:
        return False,u'无法获取更新文件'
    diff_file_cmd=''' cat /tmp/.git909081 |awk '/^[DMRCT]/{print $NF}' >/tmp/.git_diff '''
    logfunc(diff_file_cmd)
    res=os.system(diff_file_cmd)
    if res !=0:
        logfunc('更新失败,无法或取更新文件,从/tmp/.git909081')
        return False,u'更新失败'
    result=upload_code(local_repo_dir+'/'+code_dir,'/tmp/.git_diff',deploy_passwd,deploy_target,exclude_dir)
    if not result:
        return False,u'上传更新文件到目标服务器失败!!'
    r,update_log=commands.getstatusoutput('cat /tmp/.git909081')
    R=insert_deploy_log(repoName,last_version,deploy_target,envType,deploy_person,datetime.now(),update_log)
    if not R:
        return True,u'发布成功,写入发布日志失败'
    return True,u'发布成功'



'''
svn代码发布方法
'''

def svn_deploy(repoName,checkDir,user,password,repo_address,deploy_target,exclude_dir,envType,now_version,deploy_passwd,deploy_person):
    code_dir=''
    if not checkDir.startswith('/'):
        checkDir="/"+checkDir
    if checkDir.endswith('/'):
        num=checkDir.rfind('/')
        checkDir=checkDir[:num]
    if repo_address.endswith('/'):
        num=repo_address.rfind('/')
        repo_address=repo_address[:num]
    num=repo_address.rfind('/')
    code_dir=repo_address[num+1:]
    local_repo_dir=checkDir+"/"+repoName+'_'+envType
    svn_opt=' --non-interactive --username="%s" --password="%s" %s ' %(user,password,repo_address)
    if not os.path.exists(local_repo_dir):
        os.system('mkdir -p %s' %local_repo_dir)
    chk_cmd='''cd %s &&  svn checkout --force %s && cd %s && svn cleanup ''' %(local_repo_dir,svn_opt,code_dir)
    logfunc(chk_cmd)
    res=os.system(chk_cmd)
    if res != 0:
        logfunc('SVN ---- ERROR: 获取代码失败 !')
        return False,u'获取代码失败'
    #update_cmd='''cd %s && svn update --force -r%s %s  ''' %(local_repo_dir,now_version,svn_opt)
    #res=os.system(update_cmd)
    get_last_ver_cmd='''svn info %s |grep Last|grep Rev|tr -s " "|awk '{print $NF}' ''' %svn_opt
    logfunc('SVN ---- '+get_last_ver_cmd)
    r,last_version=commands.getstatusoutput(get_last_ver_cmd)
    logfunc('运行获取代码版本信息命令......  执行结果代码： %s' %r)
    logfunc('now_version:    %s last_version:   %s  ' %(now_version,last_version))
    if r==0:
        if int(last_version)==int(now_version):
            logfunc(get_last_ver_cmd+'SVN ---- Warning: no update code')
            return False,u'没有代码可更新'
        if int(last_version)>int(now_version):
            update_cmd=''' cd %s/%s && svn diff --username="%s" --password="%s" -r%s:%s --summarize|sed "s/^\s\+//g" >/tmp/.tmp9090123 2>/dev/null ''' %(local_repo_dir,code_dir,user,password,now_version,last_version)
            logfunc(update_cmd)
            res=os.system(update_cmd)
            if res != 0:
                logfunc('SVN ---- ERROR: 获取更新文件失败 \n')
                return False,u'获取更新文件失败'
            else:
                logfunc('SVN --- 获取更新文件 success ')
                get_diff_cmd='''cat /tmp/.tmp9090123|egrep -v '^$' |awk '/^[^D]/ {print $2}' >/tmp/.tmp_diff 2>/dev/null '''
                os.system(get_diff_cmd)
                logfunc('SVN ----- Get rsync diff Files '+get_diff_cmd)
                d_r=upload_code(local_repo_dir+'/'+code_dir,'/tmp/.tmp_diff',deploy_passwd,deploy_target,exclude_dir)
                if d_r:
                    r,update_log=commands.getstatusoutput('cat /tmp/.tmp9090123')
                    R=insert_deploy_log(repoName,last_version,deploy_target,envType,deploy_person,datetime.now(),update_log)
                    if not R:
                        return True,u'发布成功,写入发布日志失败'
                    return True,u'发布成功'
                else:
                    return False,u'发布失败'
        return False,u'当前版本大于远程库版本号！'
    logfunc('SVN ------ ERROR: 无法获取最新版本信息')
    return False,u'无法获取最新版本'


def upload_code(home_dir,update_file_path,deploy_passwd,deploy_path,exclude_dir_file=''):
    exclude_list=exclude_dir_file.strip(' ').split(';')
    exclude_args=deal_with_exclude(exclude_dir_file)
    if not os.path.exists(home_dir):
        logfunc('ERROR: 不存在本地checkout目录')
        return False
    up_cmd='''rsync -avlP %s  --files-from=%s %s  %s && echo ok >/tmp/.tmp0001 || echo error >/tmp/.tmp0001 ''' %(exclude_args,update_file_path,home_dir,deploy_path)
    logfunc(up_cmd)
    f=open('/tmp/.update.sh','w')
    f.write(up_cmd)
    f.close()
    ch=pexpect.spawn('bash /tmp/.update.sh')
    res=ch.expect(['yes','assword',pexpect.EOF,pexpect.TIMEOUT],timeout=120)
    if res == 0:
        ch.sendline('yes')
        ch.expect(['assword',pexpect.EOF,pexpect.TIMEOUT],timeout=120)
        ch.sendline(deploy_passwd)
        loopfunc(ch.pid)
        ch.close(force=True)
    elif res == 1:
        ch.sendline(deploy_passwd)
        loopfunc(ch.pid)
        ch.close(force=True)
    else:
        logfunc('ERROR: 执行rsync 同步代码超时,或者 远程主机URL格式错误')
        return False
    status=os.system('grep ok /tmp/.tmp0001 &>/dev/null')
    if status == 0:
        logfunc('Success: 上传代码成功')
        return True
    else:
        logfunc('SVN ----- 上传代码到环境失败！！！')
        return False


def insert_deploy_log(repoName,now_version,deploy_target,deploy_env,deploy_person,deploy_date,update_log):
    deploy=DeployInfo(repoName,now_version,deploy_target,deploy_env,deploy_person,deploy_date,update_log)
    global Update_File
    f=open(Update_File,'a')
    r,dt=commands.getstatusoutput(r'date +"%Y-%m-%d %H:%M:%S"')
    f.write(dt+'----------'+repoName+'\n')
    f.write(update_log+'\n')
    f.close()
    os.system('echo "%s" >/tmp/.update.log' %update_log)
    cmd=''' cat /tmp/.update.log|sed 's/[^a-zA-Z0-9[:punct:]]//g'|egrep -v '^$' '''
    r,update_log=commands.getstatusoutput(cmd)
    db.session.add(deploy)
    try:
        db.session.commit()
    except:
        logfunc('ERROR: 插入发布日志失败')
        return False
    logfunc('Success: 插入发布日志成功')
    return True
    




'''
循环检测函数
'''
def loopfunc(pid):
    cmd=''' pstree -p|grep python|grep '%s' |grep rsync ''' %pid
    logfunc(cmd)
    while True:
        res=os.system(cmd)
        if res != 0:
            break;
        else:
            time.sleep(3)
    
        
'''
日志记录函数
'''

def logfunc(log_str):
    global Log_File,TIMEFORMAT
    logfile=open(Log_File,'a')
    dt=time.strftime(TIMEFORMAT,time.localtime())
    logfile.write(dt+'\n')
    logfile.write(log_str+'\n')
    logfile.close()



    
    




    




