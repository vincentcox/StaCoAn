import math
i=1
while i <101:
    print(".grade-"+str(i)+"{color:rgb("+str(0+int((255/100)*i))+","+str(max(255-int((255/50)*i), 0))+" , "+str(max(255-int((255/100)*i), 0))+")}")
    i = i+1