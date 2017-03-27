'''
from Treefeature import parsesentencs
MDs=['you go * school, but I don not. * it correct?','She need * sleep']
kans=['to...Is','to']

MDpar,MDkp,MDcont, MDpar2 = parsesentencs(MDs,kans)'''
Mp = 'dafddf ***dsfadsljf'
Mk = '***4'
mp = Mp.split('***')
tmp = Mk.split('***')
mk = []
for mi in tmp:
    mj = mi.split(',')
    if mi==['']:
        mj = []
    else:
        mj = [int(i) for i in mi]
    mk.append(mj)
print mp
print mk
'''
str1 = ''
a = [[1,2],[3]]
for i in range(len(a)):
    if i != len(a)-1:
        str1 = str1+','.join(str(e) for e in a[i])+'***'

    else:
        str1 = str1+','.join(str(e) for e in a[i])
print str1
'''