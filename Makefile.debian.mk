
git clone https://github.com/eiselekd/libgit2.git
git clone https://github.com/eiselekd/pygit2.git
(cd libgit2; make -f Makefile.debign.mk)
sudo dpkg -i libgit2-27_0.27.7+dfsg.1-0.1_amd64.deb  libgit2-dev_0.27.7+dfsg.1-0.1_amd64.deb
(cd libgit2; python setup.py install --user)
