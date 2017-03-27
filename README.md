

Wei sicong  in 20/03/2017

my main code about django is at /web_application_for_gaokao_setence_correction/itemrtweb/views

the code about html is at /web_application_for_gaokao_setence_correction/templates

the code about search is at /web_application_for_gaokao_setence_correction/search

//to set up the web_application

//command line in mac os(unix)
1  sudo install pip

2  sudo pip install python==2.7

3  sudo pip install django=1.7.11

4  down load mysql at https://dev.mysql.com/downloads/mysql/

5  connect the mysql database to django in: /itemrtproject/setting.py

6  cd to the path of mysql: PATH="$PATH":/usr/local/mysql/bin

7  mysql -u "your mysql username" -p

8  enter your password

9  mysql>create database "new database name"

10 mysql>use "database name"

11 mysql>source /web_application_for_gaokao_setence_correction/gaokaogrammar.sql

12 cd to web_application_for_gaokao_setence_correction

13 python manage.py syncdb

14 python manage.py runserer





//command line in ubuntu(linux)

1  sudp apt-get install python-pip

2  sudo pip install python==2.7

3  sudo pip install django=1.7.11

4  sudo apt-get install mysql-server

5  connect the mysql database to django in: /itemrtproject/setting.py

7  mysql -u "your mysql username" -p

8  enter your password

9  mysql>create database "new database name"

10 mysql>use "database name"

11 mysql>source /web_application_for_gaokao_setence_correction/gaokaogrammar.sql

12 cd to web_application_for_gaokao_setence_correction

13 python manage.py syncdb

14 python manage.py runserer




if you have any questions about my web_application or environment building, please conntact me:

446713517@qq.com
