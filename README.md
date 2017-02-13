# py-explore
Pyhon debuging tool

usage:
```
import  explore 

explore.stop() # <-- add in place to stop programm for debug
```

OR

```
explore.handle_error(function, [args, [kvargs]]) # <-- stop and debug on exception in curren executed function
```
OR 
```
try:
   YOURE
   CODE
except:
   explore.from_traceback() # <-- stop and debug on exception
```


Then you may inspect code by regular python commands or use special commands below:

+ info:   Print this help
+ down:   Down one level in runtime stack
+ exit:   Break programm and exit
+ go:     Resume execute program
+ stack:  Show current runtime stack
+ goend:  Resume execute and cancel current breakpoint
+ gowhere [condition]:    If stop-point in cicle, stop when [condition] is true
+ up:     Up one level in runtime stack

