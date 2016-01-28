from models import RepoInfo,DeployInfo
from app import db
from sqlalchemy import desc
import os,commands,time,pexpect,re

Log_File='/tmp/deploy.log'
TIMEFORMAT='%Y-%m-%d %X'


def get_deploy_info(repoName,envType):
    repo=db.session.query(RepoInfo).filter(RepoInfo.repo_name=repoName).first()
    pass
    last_deploy=db.session.query(DeployInfo).filter(DeployInfo.repo_name=repoName).filter(DeployInfo.deploy_env=envType).order_by(Deploy_info.id.desc()).first()
    if last_deploy is not None:
        if repo.repo_type=='git':
            if envType=='test':
                pass
            else:
                pass
        else repo.repo_type=='svn':
            if envType=='test':
                pass
            else:
                pass
    else:
        return False
       



def check_deploy_passwd(repoName,envType,passwd):
    repo=db.session.query(RepoInfo).filter(RepoInfo.repo_name=repoName).first()
    REX=r'(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[0-9]{1,2})(\.(25[0-5]|2[0-4][0-9]|1[0-9][0-9]|[0-9]{1,2})){3}'
    deploy_path=''
    if repo is not None:
        if envType=='test':
            deploy_path=repo.test_deploy_path.encode('utf-8')
        else:
            deploy_path=repo.online_deploy_path.encode('utf-8')
        ip=re.search(REX,deploy_path).group()
        return check_ssh_passwd(passwd,ip)
    return False

def check_ssh_passwd(passwd,ip):
    ch=pexpect.spawn('ssh root@%s ' %ip)
    res=ch.expect(['yes','assword',pexpect.EOF,pexpect.TIMEOUT],timeout=120)
    if res==0:
        ch.sendline('yes')
        r=ch.expect(['assword',pexpect.EOF,pexpect.TIMEOUT],timeout=120)
        if r==0:
            ch.sendline(passwd)
            z=ch.expect(['assword','#',pexpect.EOF,pexpect.TIMEOUT],timeout=120)
            if z==0:
                ch.close(force=True)
            if z==1:
                ch.close(force=True)
                return True
        return False
   if res==1:
       ch.sendline(passwd)
       r=ch.expect(['assword','#',pexpect.EOF,pexpect.TIMEOUT],timeout=120)
       if r==0:
           ch.close(force=True)
       if r==1:
           ch.close(force=True)
           return True
       return False
   return False



def git_deploy():
    pass



def check_svn_validated(user,password,url):
    svn_cmd=''' svn info --non-interactive  --username="%s" --password="%s" %s &>/tmp/.svn_32197''' %(user,password,url)
    result=os.system(svn_cmd)
    if result==0:
        return True,'ok'
    res=os.system('grep URL /tmp/.svn_32197')
    if res==0:
        return False,'bad url'
    res=os.system('grep Password /tmp/.svn_32197')
    if res==0:
        return False,'bad password'
    else:
        return False,'bad username'





def svn_deploy(repoName,checkDir,user,password,repo_address,deploy_target,exclude_dir,envType,now_version):
    update_log=''
    new_version=''
    if not checkDir.startwith('/'):
        checkDir="/"+checkDir
    if checkDir.endswith('/'):
        num=checkDir.rfind('/')
        checkDir=checkDir[:num]
    local_repo_dir=checkDir+"/"+repoName+envType
    svn_opt=' --non-interactive --username="%s" --password="%s" %s ' %(user,password,repo_address)
    if not os.path.exists(local_repo_dir):
        os.system('mkdir %s' %local_repo_dir)
    chk_cmd='''cd %s &&  svn checkout --force %s &>>%s && svn cleanup ''' %(local_repo_dir,svn_opt,Log_File)
    logfunc(chk_cmd)
    res=os.system(chk_cmd)
    if res !=0:
        logfunc('ERROR: failed checkout !')
    #update_cmd='''cd %s && svn update --force -r%s %s  ''' %(local_repo_dir,now_version,svn_opt)
    #res=os.system(update_cmd)
    get_last_ver_cmd='''svn info %s ||sed -r -n "s/.*:[[:space:]]([1-9][0-9]+$).*/\\1/p"|awk "NR==2" '''
    r,last_version=commands.getstatusoutput(get_last_ver_cmd)
    if r==0:
        if int(last_version)==int(now_revision):
            logfunc(get_last_ver_cmd+' Warning: no update code')
            return 'no_update'
        elif int(last_version)>int(now_version):
            update_cmd=''' cd %s && svn diff -r%s:%s --summarize|sed "s/^\s\+//g" >/tmp/.tmp9090123 2>/dev/null ''' %(now_version,last_version)
            logfunc(update_cmd)
            res=os.system(update_cmd)
            if res !=0:
                logfunc('ERROR: Failed to get diff files')
                pass
            #upload_func()-----------
        else:
            return 'error'
    else:
        return 'cmd_error'

        

def logfunc(log_str):
    global Log_File,TIMEFORMAT
    logfile=open(Log_File,'a')
    dt=time.strftime(TIMEFORMAT,time.localtime())
    logfile.write(dt+'\n')
    logfile.write(log_str+'\n')
    logfile.close()



    
    




    




