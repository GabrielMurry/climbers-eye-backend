import time

def startTimer() -> float:
    return time.time()

def endTimer(name: str, startTime: float) -> None:
    print(name, time.time()-startTime)