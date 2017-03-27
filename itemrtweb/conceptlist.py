def concepttags(name):
    datatxt = open(name, 'r').readlines()
    datafeature = []
    dataclass = []
    N=len(datatxt)
    for i in range(0,N):
        w=datatxt[i].split(";")
        lw = len(w)
        datafeature.append(w[:lw-1])
    return datafeature

def taglist(answer):
    tag = []
    confeature = concepttags('conceptindex.txt')
    for i in answer:
        for cell in confeature:
            if i in cell:
                tag.append(cell[0])
    return tag

def concept(answers):
    #concepts = []
    answers = answers.split("...")
    answers = [cell.lower() for cell in answers]
    tag = taglist(answers)
    return tag, answers