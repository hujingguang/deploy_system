#!/bin/bash - 
#===============================================================================
#
#          FILE: deploy_supply_test.sh
# 
#         USAGE: ./deploy_supply_test.sh 
# 
#   DESCRIPTION: 
# 
#       OPTIONS: ---
#  REQUIREMENTS: ---
#          BUGS: ---
#         NOTES: ---
#        AUTHOR: YOUR NAME (), 
#  ORGANIZATION: 
#       CREATED: 03/03/2016 14:18
#      REVISION:  ---
#===============================================================================
deploy_database_ip='x.x.x.x'
deploy_database_user=test
deploy_database_passwd=test
deploy_database_name='deploy'
Test_Env_IP='x.x.x.x'
repo_name='supply'
checkout_dir='/root/tools/repos/'$repo_name'_test'
target=`mysql -u ${deploy_database_user} -p${deploy_database_passwd} -h ${deploy_database_ip} -e 'use '${deploy_database_name}';select test_deploy_path from repos_info where repo_name="'${repo_name}'"'|awk 'NR>1' `
repo_path=`mysql -u ${deploy_database_user} -p${deploy_database_passwd} -h ${deploy_database_ip} -e 'use '${deploy_database_name}';select repo_address from repos_info where repo_name="'${repo_name}'"'|awk 'NR>1' `
repo_name=`mysql -u ${deploy_database_user} -p${deploy_database_passwd} -h ${deploy_database_ip} -e 'use '${deploy_database_name}';select repo_name from repos_info where repo_name="'${repo_name}'"'|awk 'NR>1' `
exclude_dir=`mysql -u ${deploy_database_user} -p${deploy_database_passwd} -h ${deploy_database_ip} -e 'use '${deploy_database_name}';select exclude_dir from repos_info where repo_name="'${repo_name}'"'|awk 'NR>1' `
last_version=`mysql -u ${deploy_database_user} -p${deploy_database_passwd} -h ${deploy_database_ip} -e 'use '${deploy_database_name}';select now_version from deploy_info where repo_name="'${repo_name}'" and deploy_env="test" order by id desc limit 1;' |awk 'NR>1'`
if [ ! -e $checkout_dir ]
then
    mkdir -p $checkout_dir
fi

if [ ! -e ${checkout_dir}/${repo_name}/.git ]
then
    cd ${checkout_dir} && git clone $repo_path &>/tmp/.clone
    if [ $? != 0 ]
    then
      echo -e '\033[31m 克隆代码失败!!  \033[0m' 
      echo '----------------------'
      cat /tmp/.clone
      echo '----------------------'
      exit 1
  fi
fi

cd ${checkout_dir}/${repo_name} && git pull origin master &>/tmp/.pull
if [ $? != 0 ]
then
    echo -e '\033[31m 拉取代码失败 \033[0m'
    echo '------------------------'
    cat /tmp/.pull
    echo '-------------------------'
    exit 1
fi
new_version=`cat ${checkout_dir}/${repo_name}/.git/refs/heads/master` 
new_version=`echo ${new_version:0:12}`
last_version=`echo ${last_version:0:12}`

if [ "$last_version" == "$new_version" ]
then
   echo -e '\033[34m 没有代码可更新 \033[0m' 
   exit
fi

cd ${checkout_dir}/${repo_name} && git diff --name-status  $new_version $last_version >/tmp/.diff.txt
cd ${checkout_dir}/${repo_name} && git diff --name-status --diff-filter='D|C|M|R|T' $new_version $last_version|awk '{print $NF}' >/tmp/.diff

echo '修改的文件如下：'
echo '--------------------'
cat /tmp/.diff
echo -e '\033[32m 准备上传代码到测试环境 \033[0m'
rsync -avlP --exclude={'.git','.gitignore','upload','.env','storage'} --files-from=/tmp/.diff ${checkout_dir}/${repo_name} ${Test_Env_IP}:/webdata/webdir/d.xxxx.com &>/tmp/.rsync.txt

if [ $? != 0 ]
then
    echo -e '\033[31m 上传失败 \033[0m'
    echo -e '\033[31m 错误信息如下 \033[0m'
    echo  '--------------------------------'
    cat /tmp/.rsync.txt
    echo  '--------------------------------'
    exit
fi
echo -e '\033[32m 发布成功 \033[0m'

Date=`date +"%Y-%m-%d %H:%M:%S"`
files=`cat /tmp/.diff.txt`

sql='use '${deploy_database_name}';insert into deploy_info(repo_name,now_version,deploy_target,deploy_env,deploy_person,deploy_date,update_log) values("'${repo_name}'","'$new_version'","'$target'","test","root","'$Date'","'$files'");'

mysql -u ${deploy_database_user} -p${deploy_database_passwd} -e "$sql" -h ${deploy_database_ip}

if [ $? != 0 ]
then
    echo -e '\033[31m 插入发布日志失败！！！ \033[0m'
    exit 1
fi

echo -e '\033[32m 插入发布日志成功 \033[0m'



