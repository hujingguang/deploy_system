#!/usr/bin/python
from flask import Flask,render_template,request,session,flash,redirect,url_for,g,Blueprint
#from flask import *
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager,login_user,logout_user,current_user,login_required
from app import app,db,lm
from app.models import User,RepoInfo,DeployInfo
from flask.ext.paginate import Pagination
mod=Blueprint('views',__name__)

bootstrap=Bootstrap(app)

@lm.user_loader
def load_user(uid):
    return User.query.get(int(uid))

@app.before_request
def before_request():
    g.user = current_user




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
    if request.method=='GET':
        return render_template('add-repo.html',form=form)
    if form.validate_on_submit():
        repo=RepoInfo.query.filter_by(repo_name=form.repo_name.data.lower()).first()
        if repo is not None:
            form.repo_name.errors.append("the repo_name has exist !!")
            return render_template('add-repo.html',form=form)
        repo=RepoInfo(form.repo_name.data,form.repo_address.data,form.repo_user.data,form.repo_passwd.data,form.local_checkout_path.data,form.repo_type.data,form.remote_deploy_path.data,form.test_deploy_path.data,form.exclude_dir.data)
        db.session.add(repo)
        db.session.commit()
        return redirect(url_for('display_repos_info')) 
    else:
        return render_template('add-repo.html',form=form,failed_auth=True) 
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



@app.route('/list/deployinfo')
@login_required
def display_deploy_info():
    pass
    


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

