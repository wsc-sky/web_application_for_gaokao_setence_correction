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
sql2 = "SELECT * FROM newquestion"
cursor.execute(sql2)
#newquestion = cursor.fetchall()

for row1 in question:
    Qid = row1[0]
    choices = row1[8].replace(";","...")+";"+row1[9].replace(";","...")+";"+row1[10].replace(";","...")+";"+row1[11].replace(";","...")
    choices.replace("'","\'")
    try:
        execStr = 'UPDATE newquestion SET choice="{}" WHERE id={}'.format(choices, Qid)
        if Qid == 971:
            print execStr
        cursor.execute(execStr)
        db.commit()
    except:
        db.rollback()