import traceback
import sys
import inspect

try: input = raw_input
except NameError: pass

COMMANDS={'go':'go:\tResume execute program',
          'goend':'goend:\tResume execute and discart current breakpoint',
          'info':'info:\tPrint this help',
          'exit':'exit:\tFinish programm',
          'gowhere ':'gowhere [condition]:\tIf stop-point in cicle, stop when [condition] is true',
          'up':'up:\tUp one level', 
          'down':'down:\tDown one level',
          'stack':'stack:\tShow stack',
          }
          
WELCOME=True
def welcome():
    global WELCOME
    if WELCOME:
        print ("Type 'info' for help")
        WELCOME=False


LOC,GLOB=None,None
DISCART_POINTS=[]
CONDITION_POINTS={}

def completer(text,state):
    global LOC,GLOB,COMMANDS
    if LOC==None or GLOB==None: return None
    #TODO find [+,-,/,*] in text and take end of string
    m = re.match('^([^\n]*[*-+\/]{1})([^*+-\/]+$)',text)
    begin=''
    if m!=None:
      print (m.groups())
      begin=m.group(1)
      text=m.group(2)
    match=[]
    if '.' in text:
        #attrs
        n=text.rfind('.')
        objname=text[:n]
        attrpath=text[n+1:]
        try:
            obj=eval(objname,GLOB,LOC)
        except (SystemError, KeyboardInterrupt) as e: raise
        except:
            return None
        for attr in dir(obj):
            if attr.startswith(attrpath):
                match.append('%s%s.%s' % (begin,objname,attr))
    else:
        #vars
        for varlist in (COMMANDS.keys(), LOC.keys(), GLOB.keys(), keyword.kwlist):
            for var in varlist:
                if not var in match and var.startswith(text):
                    match.append(begin+var)                                      
    match.sort()
    try:
        return match[state]
    except IndexError:
        return None

def stop():
    frame = sys._getframe()
    stack=[]
    while frame: 
        stack.append(frame)
        frame=frame.f_back
    return navigate(stack[1:])
    
def handle_error(fn,*ar,**kw):
    try:
       fn(*ar,**kw)
    except (SystemError, KeyboardInterrupt) as e: raise
    except: 
       print (from_traceback())

    
def from_traceback():
    print (traceback.format_exc())
    tb=sys.exc_info()[2]
    stack=[]
    while tb:
        stack.append(tb.tb_frame)
        tb=tb.tb_next
    stack.reverse()
    return navigate(stack)
    
def set_env(stack, level):
    global LOC,GLOB,COMMANDS,DISCART_POINTS
    
    frame=stack[level]
    
    LOC= frame.f_locals
    GLOB = frame.f_globals
    point = '%s:%s' % (frame.f_code.co_filename,frame.f_lineno)
    return frame , point   
    
def navigate(stack):
    global LOC,GLOB,COMMANDS,DISCART_POINTS
        
    level=0
    frame, point=set_env(stack, level)
    
    if point in DISCART_POINTS:
        return
    if point in CONDITION_POINTS:
        try:
          r=eval(CONDITION_POINTS[point],frame.f_locals,frame.f_globals)
          if not r: return
        except (SystemError, KeyboardInterrupt) as e: raise
        except: 
          print (traceback.format_exc())
          #stop on error
        CONDITION_POINTS.pop(point)  

    welcome()    
    while True:
      line=input(point[-20:]+'>')
      
      if line in ('go','goend'): 
          if line=='goend': DISCART_POINTS.append(point)
          LOC,GLOB=None,None
          break
          
      elif line == 'up': 
          if level>=len(stack):
             print ('No up level' )
          level+=1
          frame,point=set_env(stack, level)
          
      elif line == 'down': 
          if level<=0:
             print ('No down level' )
          level+=-1
          frame,point=set_env(stack, level)
      
      elif line =='stack': 
          st=[]
          for xlevel in range(len(stack)):
             xframe=stack[xlevel]
             l=' \t%s:%s' % (xframe.f_code.co_filename,xframe.f_lineno)
             if xlevel==level:
                l='>'+l[1:]
             st.append(l )
          st.reverse()
          print ('\n'.join(st))

      elif line=='info':
          for i in COMMANDS:
            print (COMMANDS[i])
      elif line=='exit':
          sys.exit(0)
      elif line.startswith('gowhere '):
          cond=line[len('gowhere '):]
          try:
            obj=eval(cond,GLOB,LOC)
            CONDITION_POINTS[point]=cond
            LOC,GLOB=None,None
            break
          except (SystemError, KeyboardInterrupt) as e: raise
          except:
             print (traceback.format_exc())
      elif len(line)>1 and line[-1]=='?':
          #inspect object
          inspect_obj(line[:-1])
      else:
          execute(line)  

def inspect_obj(line):
    try:
       obj=eval(line,GLOB,LOC)
    except (SystemError, KeyboardInterrupt) as e: raise
    except:
       print ("Object '%s' not found" % line)
    else:
       try: print ('\t',obj.__class__)
       except AttributeError: pass
       try: print ('\t',inspect.getabsfile(obj))
       except (NameError, TypeError): pass
       if inspect.isfunction(obj):
          print ('\tDefinition: ' + obj.__name__ + inspect.formatargspec(*inspect.getargspec(obj)))
       print (' ',obj.__doc__)
       
def execute(line):
    global LOC,GLOB
    if not re.match('^[a-zA-Z0-9]*[\=]{1}',line) and not (line.startswith('print') or line.startswith('import')):
       line = 'print (repr(' + line +'))'
    try:
      exec (line , LOC,GLOB)
    except (SystemError, KeyboardInterrupt) as e: raise
    except:
      print (traceback.format_exc())

try:
    import readline
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer)
    import re,keyword
except ImportError:
    pass    


