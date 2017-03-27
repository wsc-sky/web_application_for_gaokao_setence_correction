import MySQLdb

db = MySQLdb.connect(host="localhost", user="root", passwd="1234", db="jackson")

# prepare a cursor object using cursor() method
cursor = db.cursor()
# execute SQL query using execute() method.
sql = "SELECT * FROM question"
# execute SQL query using execute() method.
cursor.execute(sql)
# Fetch all the rows in a list of lists.
question = cursor.fetchall()
db = MySQLdb.connect(host="localhost", user="root", passwd="1234", db="gaokao2")

# prepare a cursor object using cursor() method
cursor = db.cursor()
sql2 = "SELECT * FROM itemrtdb_question"
cursor.execute(sql2)
#newquestion = cursor.fetchall()


for row1 in question:
    Qid = row1[0]
    Topic = row1[3]
    idt=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14]
    newidt=[0,10,12,2,5,8,5,6,4,4,4,11,1,13,4]
    for id in idt:
        if Topic==id:
            newTopic = newidt[id]
    try:
        execStr = 'UPDATE itemrtdb_question SET topic_id={} WHERE id={}'.format(newTopic, Qid)
        if Topic == 1:
            print execStr
        cursor.execute(execStr)
        db.commit()
    except:
        db.rollback()