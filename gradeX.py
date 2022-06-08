#TODO
# - ADD C++ SUPPORT
#
#
# add to git
import pymysql
import time
import threading
import os
import shutil
import subprocess
import hexdump
import sys
import javalang
import signal
import traceback
from decimal import Decimal
import paho.mqtt.client as MQTT
lock = threading.RLock()
timeout=2
MaxOutputSize=50000
def BroadcastProgress():
  client=MQTT.Client("grader1")
  client.username_pw_set('grader','csmjuGrader.')
  try:
      client.connect("localhost")
      client.publish('/grader/status','updating')
      client.close()
  except:
      print('MQTT connection Error')
      
  


  
def IamAlive():
  fp=open('./lastseen.txt','w')
  fp.write(str(time.time()))
  fp.flush()
  fp.close()
def compare_result(solution,result,tolerant):
  b_sol=solution
  b_result=result  


  lines=solution.split("\n")
  ans=""
  for line in lines:    
    ans=ans+line.rstrip(" ")+"\n"
  solution=ans.replace("\r","")
 # solution=solution.replace(" \n","\n")
 # 
  lines=result.split("\n")
  ans=""
  for line in lines:
    ans=ans+line.rstrip(" ")+"\n"
  result=ans.replace("\r","")
  result=result.replace(" \n","\n")       
  # 
  solution=solution.rstrip()
  result=result.rstrip()
  solution=solution.rstrip()
  result=result.lstrip()
  #print("----\n%s\n+++++++\n%s\n"%(":".join("{0:x}".format(ord(c)) for c in solution),":".join("{0:x}".format(ord(c)) for c in result)))
  if(tolerant=='$'):
    if(solution==result):
     #print("1",end="") 
     return(1)
    else:
     #print("0",end="")
     #print("--ORG--\n%s\n+++++++\n%s\n"%(":".join("{0:x}".format(ord(c)) for c in b_sol),":".join("{0:x}".format(ord(c)) for c in b_result)))
   
     #print("--TRM--\n%s\n+++++++\n%s\n"%(":".join("{0:x}".format(ord(c)) for c in solution),":".join("{0:x}".format(ord(c)) for c in result)))
     #print("-------------\n%s\n...................\n%s\n"%(solution,result))
     #sys.exit()
      
     return(0)
  else:
    try:
      

      if(abs(float(solution)-float(result)) < float(tolerant)):
        return(1)
      else:
        return(0)
    except:
        return(0)
      
def grading():
  cc=0
  ThreadName=threading.current_thread().name
  dirx = './sandbox/%s'%ThreadName
  print(dirx)
  if os.path.exists(dirx):
    shutil.rmtree(dirx)
  os.makedirs(dirx)
  
  while(1):
    cc=cc+1


    try:          
        db = pymysql.connect(host='localhost',user='root',password='hakino0013',database='grader_test',charset='utf8')
        #db.set_character_set('utf8')
        cursor = db.cursor()
        cursor.execute('SET NAMES utf8;')
        cursor.execute('SET CHARACTER SET utf8;')
        cursor.execute('SET character_set_connection=utf8;')
        threadLock.acquire(1)
        print("%s locking\n"%(ThreadName))
        cursor.execute("select count(*) from waitinglists")
        result=cursor.fetchone()
        if (result[0]>0 ):
            
            cursor.execute("select submission_id from waitinglists limit 0,1")
            result = cursor.fetchone()
            submission_id=result[0]
            print("%s grading %d\n"%(ThreadName ,submission_id))
            
            cursor.execute("delete from waitinglists where submission_id=%d"%submission_id)
            db.commit()
            threadLock.release()
            print("%s release %d\n"%(ThreadName ,submission_id))
           

            #--------- start grading
            cursor.execute("select id,problem_id,user_id,code,Lang,fname, schedule_id from submissions where id='%d'"%submission_id)
            result=cursor.fetchone()
            prob_id=result[1]
            login=result[2]
            code=result[3]
            lang=result[4]
            fname=result[5]
            schedule_id=result[6]
            filename='untitle.txt'
            binary='untitle.bin'
            cursor.execute("select score from schedules where id=%s",schedule_id)
            result=cursor.fetchone()
            #print("fetch")
            total_score=result[0]
            
            cursor.execute("select tolerant from problems where id=%s",prob_id)
            result=cursor.fetchone()
            
            if(cursor.rowcount>0):
              

              tolerant=result[0]             
              
            else:          
              
              #total_score=100
              tolerant='$'
              
#            print(total_score)

            #----------------- Write source code to file
            lang=lang.upper()
            if((lang=='C') or (lang=='CS') or (lang=='C#') or (lang=='C++')):
              filename="%s/%s"%(dirx,fname)
              binary='a.exe'
            if(lang=='JAVA'):
              classname='main_class_error'
              try:
               tree = javalang.parse.parse(code)
               classname = next(klass.name for klass in tree.types
                if isinstance(klass, javalang.tree.ClassDeclaration)
                for m in klass.methods
                if m.name == 'main' and m.modifiers.issuperset({'public', 'static'}))
               classname=classname.rstrip()
              except:
                classname='main_class_error'
              filename="%s/%s.java"%(dirx,classname)
              binary="%s"%(classname)
              
            if((lang=='PYTHON') or (lang=='PY') or (lang=='PYTHON3') or (lang=='PY3')):
              filename="%s/%s.py"%(dirx,fname)
              binary=filename
              
            if(lang=='RUBY'):
              filename="%s/%s.rb"%(dirx,fname)
              binary=filename            
            if(lang=='KOTLIN'):
              filename="%s/%s"%(dirx,fname)
              binary='main.jar'  
            text_file= open(filename, "w")
            text_file.write(code)
            text_file.flush()
            os.fsync(text_file.fileno())
            text_file.close()

          #---------------------------------------------
            
        #--Compile --
            if(lang=='C'):
              subprocess.call( ["sh","-c", "/usr/bin/gcc %s -lm -o %s/%s >%s/cmsg.txt"%(filename,dirx,binary,dirx)])
            if(lang=='JAVA'):
              subprocess.call( ["sh","-c", "/usr/bin/javac %s >%s/cmsg.txt"%(filename,dirx)])
            if((lang=='C#') or (lang=='CS')):
              #gmcs $folder_tmp/$fname -out:$folder_tmp/a.exe > $folder_tmp/cmsg.txt
              #print("/usr/bin/mcs %s -out:%s   >%s/cmsg.txt"%(filename,binary,dirx))
              subprocess.call( ["sh","-c", "/usr/bin/dmcs %s -out:%s/%s   >%s/cmsg.txt"%(filename,dirx,binary,dirx)])
              #sys.exit()
            if(lang=='C++'):
              subprocess.call( ["sh","-c", "/usr/bin/g++  %s -o %s/%s -lm 2>%s/cmsg.txt"%(filename,dirx,binary,dirx)])        
            if(lang=='KOTLIN'):
              subprocess.call( ["sh","-c", "/snap/bin/kotlinc  %s -include-runtime -d %s/%s >%s/cmsg.txt"%(filename,dirx,binary,dirx)])        

            compiler_output='No data'
            print("compiler_output",compiler_output)
            print("file path XXXXX",os.path.isfile("%s/cmsg.txt"%dirx))
            if(os.path.isfile("%s/cmsg.txt"%dirx)): 
              text_file=open("%s/cmsg.txt"%dirx, "r")
              compiler_output=text_file.read()
              text_file.close
            else:
              #print("compile error")
              x=0
#            cursor.execute("update submissions set compiler_message='%s' where id='%s'"%(pymysql.escape_string(compiler_output),submission_id))
            cursor.execute("update submissions set compiler_message='%s' where id='%s'"%(compiler_output,submission_id))
            db.commit()




        #--Run & Grade --
            #todo
            # 2 catch no binary created
            # 3 catch no runtime output generated
            cursor.execute("select  input,output,id from testcases where problem_id='%s'"%prob_id)
            results=cursor.fetchall()
            totalscore=0
            counter=0
            grading_msg=""
            user_output=''
            for row in results:
              counter=counter+1
              text_file=open("%s/input.txt"%dirx, "w")
              text_file.write(row[0].rstrip())
              text_file.flush()
              os.fsync(text_file.fileno())
              text_file.close()

        #-------- Run ----------------
              #print("run")
              overtime=""
              if((lang=='C') or (lang=='CS') or (lang=='C#') or(lang=='C++')):
                p = subprocess.Popen(["sh","-c","%s/%s <%s/input.txt > %s/output.txt"%(dirx,binary,dirx,dirx)],preexec_fn=os.setsid)
                try:
                  p.wait(timeout)
                except:
                  overtime="T"
                  #print("T",end="")
                  os.killpg(os.getpgid(p.pid), signal.SIGTERM)
              if(lang=='JAVA'):
                 #print("/usr/bin/java -classpath %s %s <%s/input.txt > %s/output.txt"%(dirx,binary,dirx,dirx))
                 #sys.exit()
                 p = subprocess.Popen(["sh","-c","/usr/bin/java -classpath %s %s <%s/input.txt > %s/output.txt"%(dirx,binary,dirx,dirx)],preexec_fn=os.setsid)
                 try:
                  p.wait(timeout)
                 except:
                  overtime="T"
                  #print("T",end="")
                  os.killpg(os.getpgid(p.pid), signal.SIGTERM)
              if(lang=='KOTLIN'):               

                 p = subprocess.Popen(["sh","-c","/usr/bin/java -classpath %s -jar %s/%s <%s/input.txt > %s/output.txt"%(dirx,dirx,binary,dirx,dirx)],preexec_fn=os.setsid)
                 try:
                  p.wait(timeout)
                 except:
                  overtime="T"
                  #print("T",end="")
                  os.killpg(os.getpgid(p.pid), signal.SIGTERM)

              if((lang=='PYTHON') or (lang=='PY')):
                # exec("timeout 1s  python $folder_tmp/$fname.py < $folder_tmp/input ",$b);
                p = subprocess.Popen(["sh","-c","/usr/bin/python %s <%s/input.txt > %s/output.txt"%(binary,dirx,dirx)],preexec_fn=os.setsid)
                try:
                  p.wait(timeout)
                except:
                  overtime="T"
                  #print("T",end="")/usr
                  os.killpg(os.getpgid(p.pid), signal.SIGTERM)
              if((lang=='PYTHON3') or (lang=='PY3')):
                # exec("timeout 1s  python $folder_tmp/$fname.py < $folder_tmp/input ",$b);
                p = subprocess.Popen(["sh","-c","/usr/bin/python3 %s <%s/input.txt > %s/output.txt"%(binary,dirx,dirx)],preexec_fn=os.setsid)
                try:
                  p.wait(timeout)
                except:
                  overtime="T"
                  #print("T",end="")
                  os.killpg(os.getpgid(p.pid), signal.SIGTERM)
                  
              if(lang=='RUBY'):
                # exec("timeout 1s  python $folder_tmp/$fname.py < $folder_tmp/input ",$b);
                p = subprocess.Popen(["sh","-c","/usr/bin/ruby %s <%s/input.txt > %s/output.txt"%(binary,dirx,dirx)],preexec_fn=os.setsid)
                try:
                  p.wait(timeout)
                except:
                  overtime="T"
                  #print("T",end="")
                  os.killpg(os.getpgid(p.pid), signal.SIGTERM)
              
        #------- Grade -----------------
              
              #print("grade")
              if(os.path.isfile("%s/output.txt"%dirx)==1): 
               statinfo = os.stat("%s/output.txt"%dirx)
               text_file=open("%s/output.txt"%dirx, "r")
               if(statinfo.st_size < MaxOutputSize):
                try:
                 user_output=text_file.read()
                except:
                 print("BAD ASCII OUTPUT")
                 user_output=""
               text_file.close
               os.remove("%s/output.txt"%dirx)
               os.remove("%s/input.txt"%dirx)
              if(user_output==''):
                # no output
                score=0
                threadLock.acquire(1)
                if overtime=='T':
                  grading_msg=grading_msg+overtime
                  cursor.execute("insert into analyses(submission_id,testcase_id,output,message,created_at,updated_at) values('%s','%s','!! no output !!','%s',now(),now())"%(submission_id,row[2],overtime))
                else:
                  grading_msg=grading_msg+"X"
                  cursor.execute("insert into analyses(submission_id,testcase_id,output,message,created_at,updated_at) values('%s','%s','!! no output !!','%s',now(),now())"%(submission_id,row[2],"X"))
                db.commit()
                threadLock.release()
              else:
                score=compare_result(row[1],user_output,tolerant)
                totalscore=totalscore+score
                threadLock.acquire(1)
                if(score>0):
                  grading_msg=grading_msg+"Y"
                  cursor.execute("insert into analyses(submission_id,testcase_id,output,message,created_at,updated_at) values('%s','%s','%s','%s',now(),now())"%(submission_id,row[2],user_output,"Y"))
                else:
                  grading_msg=grading_msg+"N"
                  cursor.execute("insert into analyses(submission_id,testcase_id,output,message,created_at,updated_at) values('%s','%s','%s','%s',now(),now())"%(submission_id,row[2],user_output,"N"))
                db.commit()
                threadLock.release()
            if(counter==0):
              finalscore=0
              grading_msg='No testcase'
            else:
              finalscore=(float(totalscore)/float(counter))*float(total_score)
            print("\n%s Total score=%f\n"%(prob_id,finalscore))
            cursor.execute("update submissions set score='%f',message='%s',graded='1',output='%s' where id='%s'"%(finalscore,grading_msg,user_output,submission_id))
            db.commit()
            print("%s:%d, %s,%s ,%s,score:%f, msg:%s\n"%(ThreadName ,submission_id,login,prob_id,lang,finalscore,grading_msg))
            #if(finalscore <100):
              #print("BAD grading:"+prob_id)
    # -------------------------House keeping
            if(os.path.isfile("%s/cmsg.txt"%dirx)): 
              os.remove("%s/cmsg.txt"%dirx)
            os.remove(filename)
            if(((lang=='C') or (lang=='JAVA') or(lang=='C#') or (lang=='CS'))and os.path.isfile("%s/cmsg.txt"%dirx)):
              os.remove("%s/%s"%(dirx,binary))
            IamAlive()
#            BroadcastProgress()
              
            #break
              
            #--------- done grading
            #time.sleep(2)
        else:
            threadLock.release()
            print("%s release\n"%(ThreadName))
            if(cc>15):
              print("%s %s no submission, still alive! \n"%(ThreadName,time.strftime("%H:%M:%S")))
              cc=0
            time.sleep(5)       
            
        db.close()
        IamAlive()
        
    except Exception as e:
      print(e)
      traceback.print_exc()
      print("Ops!, database has gone away!")
      time.sleep(60)
      IamAlive()
        #break

#--------------- start grading thread --------------


threadLock = threading.Lock()

threadcount=2
#worker=[threading.Thread(target=grading) for i in range(threadcount-1)]
#for j in range(0,threadcount-1):  
#  worker[j].start()
  
grading()
##
##thread2=threading.Thread(target=grading)
##thread2.start()
##thread3=threading.Thread(target=grading)
##thread3.start()
##
##thread4=threading.Thread(target=grading)
##thread4.start()
##
##thread5=threading.Thread(target=grading)
##thread5.start()
##
##thread6=threading.Thread(target=grading)
##thread6.start()
##
##thread7=threading.Thread(target=grading)
##thread7.start()
##
##thread8=threading.Thread(target=grading)
##thread8.start()
##
##thread9=threading.Thread(target=grading)
##thread9.start()
##
##thread10=threading.Thread(target=grading)
##thread10.start()
##
##thread11=threading.Thread(target=grading)
##thread11.start()
##
##thread12=threading.Thread(target=grading)
##thread12.start()
##
##thread13=threading.Thread(target=grading)
##thread13.start()
##
##thread14=threading.Thread(target=grading)
##thread14.start()
##
##thread15=threading.Thread(target=grading)
##thread15.start()
##
##thread16=threading.Thread(target=grading)
##thread16.start()
##
##thread17=threading.Thread(target=grading)
##thread17.start()
##
##thread18=threading.Thread(target=grading)
##thread18.start()
##
##thread19=threading.Thread(target=grading)
##thread19.start()
##
##thread20=threading.Thread(target=grading)
##thread20.start()

