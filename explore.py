import traceback
import sys
import inspect
import os

try: input = raw_input
except NameError: pass

COMMANDS={
  'go':'go:\tResume program execution',
  'goend':'goend:\tResume execution and turn off current breakpoint',
  'info':'info:\tPrint this help',
  'exit':'exit:\tTry to sys.exit',
  'gowhere ':'gowhere [condition]:\tStop at this breakpoint only when [condition] is true',
  'up':'up:\tUp one level in stack',
  'down':'down:\tDown one level in stack',
  'stack':'stack:\tShow full stack',
  'stack ':'stack LEVEL:\tGo to selected level in stack',
  'save': 'save [var]:\tSave var to file',
  'whereami': 'go:\tPrint code of breakpoint',
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
            obj=eval(objname, LOC, GLOB)
        except (SystemError) as e: raise
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
    # autoselect level
    level = 0
    for lev, frame in enumerate(stack):
        filename = frame.f_code.co_filename
        # TODO pandas name
        if not 'site-packages' in filename and not 'pandas/' in filename:
            level = lev
            break
    return navigate(stack, level=level)
    
def set_env(stack, level):
    global LOC,GLOB,COMMANDS,DISCART_POINTS
    
    frame=stack[level]
    
    LOC= frame.f_locals
    GLOB = frame.f_globals
    point = '%s:%s' % (frame.f_code.co_filename,frame.f_lineno)
    return frame, point
    
def navigate(stack, level=0):
    global LOC,GLOB,COMMANDS,DISCART_POINTS
        

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
      line=input(point[-20:]+'>').strip()
      
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
          stack_len = len(stack)
          for xlevel in range(stack_len):
             xframe=stack[xlevel]
             l='%s \t%s:%s' % (xlevel, xframe.f_code.co_filename,xframe.f_lineno)
             if xlevel==level:
                l='>'+l[1:]
             st.append(l)
          st.reverse()
          print ('\n'.join(st))
      elif re.match('stack [\d]+$', line):
          lev = int(line[5:])
          if lev >= 0 and lev < len(stack):
              level = lev
          frame, point = set_env(stack, level)
      elif line=='info':
          for i in COMMANDS:
            print (COMMANDS[i])
      elif line=='exit':
          sys.exit(0)
      elif re.match('whereami [\d]+$', line) or line == 'whereami':
          window = 3
          ar = line.split(' ')
          if len(ar) > 1 and ar[1].isdigit():
              window = int(ar[1])

          fname = frame.f_code.co_filename
          lineno = frame.f_lineno
          if os.path.exists(fname):
              try:
                  with open(fname) as fd:
                      for num, line in enumerate(fd, 1):
                         if abs(lineno - num) <= window:
                            cursor = '>' if lineno == num else ' '
                            print(f'{cursor}{num}\t{line[:-1]}')
                  continue
              except OSError:
                  pass
          print(':(')
      elif line.startswith('gowhere '):
          cond=line[len('gowhere '):]
          try:
            obj=eval(cond, LOC, GLOB)
            CONDITION_POINTS[point]=cond
            LOC,GLOB=None,None
            break
          except (SystemError, KeyboardInterrupt) as e: raise
          except:
             print (traceback.format_exc())
      elif line.startswith('save '):
          obj=line[len('save '):]
          try:
            varname = re.sub('[^\w]+', '', obj)
            obj=eval(obj, LOC, GLOB)

            if isinstance(obj,bytes):
                obj = obj.decode()
            elif isinstance(obj,str):
                pass
            else:
                obj = str(obj)

            open('out{}.txt'.format(varname), 'w').write(obj)

            LOC,GLOB=None,None
            break
          except (SystemError, KeyboardInterrupt) as e: raise
          except:
             print (traceback.format_exc())
      elif len(line)>1 and line[-1]=='?':
          #inspect object
          inspect_obj(line[:-1])
      elif line == '':
          pass
      else:
          execute(line)  

def inspect_obj(line):
    try:
       obj=eval(line, LOC, GLOB)
    except (SystemError) as e: raise
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
    if not re.findall('[^\=]{1}[\=]{1}[^\=]{1}',line) and not (line.startswith('print') or line.startswith('import ') or line.startswith('from ')):
       line = 'print (repr(' + line +'))'
    try:
       exec(line, LOC, GLOB)
    except (SystemError) as e: raise
    except:
      print (traceback.format_exc())

try:
    import readline
    readline.parse_and_bind("tab: complete")
    readline.set_completer(completer)
    import re,keyword
except ImportError:
    pass    


