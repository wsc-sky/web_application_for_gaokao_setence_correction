import MySQLdb

db = MySQLdb.connect(host="localhost", user="root", passwd="1234", db="gaokao2")

# prepare a cursor object using cursor() method
cursor = db.cursor()
# execute SQL query using execute() method.
sql = "SELECT * FROM itemrtdb_question"
# execute SQL query using execute() method.
cursor.execute(sql)
# Fetch all the rows in a list of lists.
question = cursor.fetchall()
sql2 = "SELECT * FROM itemrtdb_answer"
cursor.execute(sql2)
#newquestion = cursor.fetchall()

for row1 in question:
    Qid = row1[0]
    choice = row1[2]
    choices = choice.split(";")
    answer = row1[10]
    for i in range(0,4):
        if choices[i]==answer:
            if i == 0:
                ca = 'A'
            elif i == 1:
                ca = 'B'
            elif i == 2:
                ca = 'C'
            else:
                ca = 'D'

    try:
        execStr = 'INSERT INTO itemrtdb_answer (id,question_id,content,correctness) VALUES ({},{},\'{}\',1.00)'.format(Qid,Qid,ca)
        print execStr
        cursor.execute(execStr)
        db.commit()
    except:
        db.rollback()