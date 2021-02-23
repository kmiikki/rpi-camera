def inputYesNo(name,question,default=True):
    if default==True:
        default_value="y"
    else:
        default_value="n"
    while True:
        try:
            tmp=input(question+" (Y/N, Default "+default_value+": <Enter>): ")        
            value=str(tmp).lower()
        except ValueError:
            print("Invalid input!")
            continue
        else:
            if (value==""):
                s="Default selected: "+name+" "
                if default_value=="y":
                    s+="enabled"
                    value="y"
                else:
                    s+="disabled"
                    value+="n"
                print(s)
                break
            if (value=="y"):
                print(name+" enabled")
                break
            if (value=="n"):
                print(name+" disabled")
                break
            print ("Select Y or N!")
            continue
    if value=="y":
        return True
    else:
        return False

def inputListValue(name,listValues=[],default=-1,listErrorText="Not a valid value!",strType=False,strUpper=False):
    if not default in listValues:
        import sys
        print("\nDefault value "+str(default)+" not in:")
        print(str(listValues))
        print("The program is terminated!")
        sys.exit(1)
    list_str=""
    for i in range(len(listValues)):
        list_str+=str(listValues[i])
        if i<len(listValues)-1:
            list_str+=", "
        else:
            list_str+="; "    
    while True:
        value=default
        try:
            tmp=input("Select "+name+" ("+list_str+"Default="+str(default)+"): ")
            if strType:
                if strUpper:
                    tmp=tmp.upper()
                value=tmp
            else:
                value=int(tmp)
        except ValueError:
            if (tmp==""):
                value=default
                print("Default value selected: "+str(value))
                break
            print("Not a valid number!")
            continue
        else:
            if strType and tmp=="":
                value=default
                print("Default value selected: "+value)
                break
            if not value in listValues:
                print("Not a valid "+name+" value!")
                continue
            break
    return value


def inputValue(name,minValue=0,maxValue=1,default=0,unit="",rangeErrorText="Value out of range",intMode=True):
    while True:
        value=default
        try:
            s="Select "+name+" ("+str(minValue)+"..."+str(maxValue)
            if not unit=="":
                s+=" "+unit
            s+=", Default="+str(default)+": <Enter>): "
            tmp=input(s)
            if intMode:
                value=int(tmp)
            else:
                value=float(tmp)
        except ValueError:
            if (tmp==""):
                print("Default value selected: "+str(value))
                break
            print("Not a valid number!")
            continue
        else:
            if value<minValue or value>maxValue:
                print(rangeErrorText)
                continue
            break
    return value

