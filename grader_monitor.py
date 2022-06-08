import psutil
import subprocess
import time
# Iterate over all running process
timeout=180
def StartGrader():
    GraderExist=0
    for proc in psutil.process_iter():
        try:
            # Get process name & pid from process object.
            processName = proc.name()
            processCmd=proc.cmdline()
            processID = proc.pid
            #print(processID,processCmd)
            if(len(processCmd)==2):
                if((processCmd[0]=='/usr/bin/python3' ) & (processCmd[1]=='/home/ohm/grader/gradeX.py')):
                    GraderExist=1
                    print("Kill grader!")
                    proc.kill()
                    time.sleep(2)
                    print("Start Grader!")
                    subprocess.Popen(['/usr/bin/screen','-dmS','grader_screen','/usr/bin/python3','/home/ohm/grader/gradeX.py'])
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    if(GraderExist==0):
        print("Start Grader!")
        subprocess.Popen(['/usr/bin/python3','./gradeX.py'],shell=True)
#while(True):

StartGrader()
lockcounter=0
grader_time=0
while(True):
    fp=open('./lastseen.txt','r')
    msg="init"
    try:
        msg=fp.readline()
        grader_time=float(msg)
    except Exception:
        time.sleep(1)
        lockcounter=lockcounter+1
        print("Ops! %d %s"%(lockcounter,msg))
        if(lockcounter>3):
            print("Heart beat stop")
            grader_time=0
            lockcounter=0
    if(abs(time.time()-grader_time) > 180):
        StartGrader()
    time.sleep(60)
