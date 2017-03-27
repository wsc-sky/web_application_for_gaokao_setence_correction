import MySQLdb
from Treefeature import parsesentencs
# coding = gbk
db = MySQLdb.connect(host="localhost", user="root", passwd="1234", db="enggrammar")

# prepare a cursor object using cursor() method
cursor = db.cursor()
# execute SQL query using execute() method.
sql = "SELECT * FROM itemrtdb_question"
# execute SQL query using execute() method.
cursor.execute(sql)
# Fetch all the rows in a list of lists.
question = cursor.fetchall()



MDs = []
kans = []
cid = []
for row in question:
    cid.append(row[0])
    MDs.append(row[1])
    kans.append(row[2])
MDpar,MDkp,MDcont, MDpar2 = parsesentencs(MDs,kans)

for id,Mp,Mk in zip(cid,MDpar2, MDkp):
    try:
        str1 = '***'.join(Mp)
        str2 = ''
        for i in range(len(Mk)):
            if i != len(Mk)-1:
                str2 = str2+','.join(str(e) for e in Mk[i])+'***'
            else:
                str2 = str2+','.join(str(e) for e in Mk[i])
        execStr = 'UPDATE itemrtdb_question SET Mp="{}",Mk="{}" WHERE id={}'.format(str1, str2, id)
        cursor.execute(execStr)
        db.commit()
    except:
        db.rollback()
