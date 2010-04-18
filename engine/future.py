from threading import *
#import copy

class Future:
    """
    Recipe 84317: Easy threading with Futures (Python)
    source: http://code.activestate.com/recipes/84317/

    Changed to fit mmda needs.
    """

    def __init__(self,func,*param):
        # Constructor
        self.__done=0
        self.__result=None
        self.__status='working'

        self.__C=Condition()   # Notify on this Condition when result is ready

        # Run the actual function in a separate thread
        self.__T=Thread(target=self.Wrapper,args=(func,param))
        self.__T.setName("FutureThread")
        self.__T.start()

    def __repr__(self):
        return '<Future at '+hex(id(self))+':'+self.__status+'>'

    def __call__(self):
        self.__C.acquire()
        while self.__done==0:
            self.__C.wait()
        self.__C.release()
        # We deepcopy __result to prevent accidental tampering with it.
        # .... or not ;-)
        #a=copy.deepcopy(self.__result)
        #return a
        return self.__result

    def Wrapper(self, func, param):
        # Run the actual function, and let us housekeep around it
        self.__C.acquire()
        try:
            self.__result=func(*param)
        except:
            self.__result="Exception raised within Future"
        self.__done=1
        self.__status=`self.__result`
        self.__C.notify()
        self.__C.release()


def timeout(func, args=(), kwargs={}, t=1.0, default=None):
    """
    http://code.activestate.com/recipes/473878/
    """
    class InterruptableThread(Thread):
        def __init__(self):
            Thread.__init__(self)
            self.result = None

        def run(self):
            try:
                self.result = func(*args, **kwargs)
            except:
                self.result = default

    it = InterruptableThread()
    it.start()
    it.join(t)
    if it.isAlive():
        return default
    else:
        return it.result

