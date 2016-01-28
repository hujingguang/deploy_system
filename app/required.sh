#!/bin/bash

pip install flask-*

pip install apr apr-util subversion subversion-devel neon neon-devel apr apr-util


#安装pysvn库
wget http://pysvn.barrys-emacs.org/source_kits/pysvn-1.7.4.tar.gz |tar -zxvf

cd pysvn-1.7.4 && python setup.py install && cd Source && python setup.py configure && make
cd ../Tests && make && cd ../Source
mkdir [YOUR PYTHON LIBDIR]/site-packages/pysvn
cp pysvn/__init__.py [YOUR PYTHON LIBDIR]/site-packages/pysvn
cp pysvn/_pysvn*.so [YOUR PYTHON LIBDIR]/site-packages/pysvn

pip install pysvn
