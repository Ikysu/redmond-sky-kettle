import pexpect
import time
import sys


if len(sys.argv) > 1:
    mac = sys.argv[1]
else:
    mac = input("MAC (00:00:00:00:00:00) >")
if len(sys.argv) > 2:
    key = sys.argv[2]
else:
    key = input("HEX UUID (ffffffffffffffff)>")

info = {
    'mode': {
        '00':"Кипячение",
        '01':"Нагрев до температуры",
        '02':"Кипячение + Нагрев до температуры",
        '03':"Ночник"
    },
    'status': {
        '00':"Выключен",
        '02':"Включен"
    }
}

ite = 0
def hh(he):
    return format(he, 'x')

def getIter():
    global ite
    nowite=hh(ite)
    if ite<100:
        ite=ite+1
    else:
        ite=0
    
    if len(nowite) == 2:
        return nowite
    else:
        return "0"+nowite



def timeInvert(data):
    out = []
    li = list(hh(data))
    le = (int)(len(li)/2)
    for i in range(0,len(li),2): out.append(li[i]+""+li[i+1])
    return "".join(list(reversed(out)))

def getTMZ(id):
    return timeInvert(id*60*60)
    
def getTime():
    return timeInvert(int(time.time()))


def hexToDec(s):
    return int(s, 16)

def getWattsAndAllTime():
    child.sendline("char-write-req 0x000e 55" + getIter() + "4700aa")
    child.expect("value: ") 
    child.expect("\r\n") 
    statusStr = child.before[0:].decode("utf-8")
    Watts = hexToDec(str(statusStr.split()[11] + statusStr.split()[10] + statusStr.split()[9]))
    alltime = round(Watts/2200, 1)
    child.expect(r'\[LE\]>')

    print("Чайник использовал "+str(Watts)+" ватт и проработал "+str(alltime))

def getTimes():
    child.sendline("char-write-req 0x000e 55" + getIter() + "5000aa")
    child.expect("value: ") 
    child.expect("\r\n") 
    statusStr = child.before[0:].decode("utf-8")
    times = hexToDec(str(statusStr.split()[7] + statusStr.split()[6]))
    child.expect(r'\[LE\]>')

    print("Чайник использовался "+str(times)+" раз(а)")

def getNowWork():
    child.sendline("char-write-req 0x000e 55" + getIter() + "06aa")
    child.expect("value: ") 
    child.expect("\r\n") 
    statusStr = child.before[0:].decode("utf-8")

    answer = statusStr.split()
    status = info['status'][answer[11]]
    temp = hexToDec(answer[8])
    mode = info['mode'][answer[3]]

    print("["+status+"] Мод: "+mode+" | "+str(temp))

def setWork(mode, temp, howMuchBoil=80):
    if mode == "01":
        if temp>35 and temp<90:
            temp = str(hh(temp))
        else:
            print("Задай температуру в пределах от 35 до 90!")
            return True;

    child.sendline("char-write-req 0x000e 55" + getIter() + "05" + mode + "00" + temp + "00000000000000000000" + str(howMuchBoil) + "0000aa")
    child.expect("value: ")
    child.expect("\r\n")
    statusStr = child.before[0:].decode("utf-8")
    answer = statusStr.split()[3]
    child.expect(r'\[LE\]>')
    if answer != "01":
        print("Ошибка :(")
    else:
        print("Настройки сохранены!")

def runKettle():
    child.sendline("char-write-req 0x000e 55" + getIter() + "03aa")
    child.expect("value: ")
    child.expect("\r\n") 
    statusStr = child.before[0:].decode("utf-8")
    answer = statusStr.split()[3]
    child.expect(r'\[LE\]>')
    if answer != "01":
        print("Ошибка :(")
    else:
        print("Начинаем кипятить водичку!")


def stopKettle():
    child.sendline("char-write-req 0x000e 55" + getIter() + "04aa")
    child.expect("value: ") 
    child.expect("\r\n") 
    statusStr = child.before[0:].decode("utf-8")
    answer = statusStr.split()[3]
    child.expect(r'\[LE\]>')
    if answer != "01":
        print("Ошибка :(")
    else:
        print("Чайник выключен!")

print("spawn")
child = pexpect.spawn("gatttool -I -t random -b " + mac, ignore_sighup=False)
child.expect(r'\[LE\]>', timeout=3)
print("connect")
child.sendline("connect")
child.expect(r'Connection successful.*\[LE\]>', timeout=3)

print("notify")
child.sendline("char-write-cmd 0x000c 0100")
child.expect(r'\[LE\]>') 

print("auth")
child.sendline("char-write-req 0x000e 55" + getIter() + "ff" + key + "aa")
child.expect("value: ")
child.expect("\r\n")
connectedStr = child.before[0:].decode("utf-8")
answer = connectedStr.split()[3] # parse: 00 - no   01 - yes
child.expect(r'\[LE\]>')
if answer != "01":
    print("AUTH ERR")
else:
    print("sync")
    child.sendline("char-write-req 0x000e 55" + getIter() + "6e" + getTime()+getTMZ(5) + "0000aa")
    child.expect("value: ")
    child.expect("\r\n")
    child.expect(r'\[LE\]>')

    print("--- SKY KETTLE ---")
    while True:
        cmd = input(">")

        if cmd == "watts" or cmd == "alltime":
            getWattsAndAllTime()
        elif cmd == "times":
            getTimes()
        elif cmd == "now":
            getNowWork()
        elif cmd == "set":
            inmode = int(input("Mode (1 - Кипячение | 2 - Нагрев) >"))
            if inmode == 1:
                setWork("00", "00")
            elif inmode == 2:
                tmp = int(input("Температура (от 35 до 90) >"))
                if tmp>35 and tmp<90:
                    setWork("01", tmp)
                else:
                    print("Задай температуру в пределах от 35 до 90!")
            else:
                print("Неправильный мод!")

        elif cmd == "run":
            runKettle()
        elif cmd == "stop":
            stopKettle()
        elif cmd == "exit" or cmd == "q" or cmd == "quit":
            print("Bye!")
            break
        else:
            print("Такой команды не существует!")
