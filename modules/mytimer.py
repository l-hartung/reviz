import time
import traceback


def measureStart():
    return time.time()


def measureEnd(start):
    end = time.time()
    name = traceback.extract_stack(None, 2)[0][2]
    diff = end - start
    print(name, "took", f"{diff:.4f}", "seconds")


def measureEnd2(start, name):
    end = time.time()
    name2 = traceback.extract_stack(None, 2)[0][2]
    diff = end - start
    print(name2, name, "took", f"{diff:.4f}", "seconds")


# from .mytimer import measureStart,measureEnd
# measure=measureStart()
# measureEnd(measure)
