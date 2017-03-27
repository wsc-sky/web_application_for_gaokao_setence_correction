import MySQLdb
# coding = gbk
db = MySQLdb.connect(host="localhost", user="root", passwd="1234", db="gaokao2", charset="utf8")

# prepare a cursor object using cursor() method
cursor = db.cursor()
# execute SQL query using execute() method.
sql = "SELECT * FROM itemrtdb_concept"
# execute SQL query using execute() method.
cursor.execute(sql)
# Fetch all the rows in a list of lists.
question = cursor.fetchall()

# prepare a cursor object using cursor() method
cursor = db.cursor()
sql2 = "SELECT * FROM itemrtdb_tag"
cursor.execute(sql2)
#newquestion = cursor.fetchall()


for row1 in question:
    cid = row1[0]
    cname = row1[1]
    print cname, cname.encode('utf8')
    try:
        cursor.execute("set character_set_database=utf8")
        cursor.execute("set names utf8;")     # <--- add this line,
        execStr = 'UPDATE itemrtdb_tag SET description="{}" WHERE concept_id={}'.format(cname.encode('utf8'), cid)
        print execStr
        cursor.execute(execStr)
        db.commit()
    except:
        db.rollback()