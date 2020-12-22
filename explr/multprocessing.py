import time
from multiprocessing import Process


def f(name):
    print("Waiting 5s")
    time.sleep(5)
    print("hello", name)


if __name__ == "__main__":
    p = Process(target=f, args=("bob",))
    p.start()
    print("Doing other things")
    p.join()
    print("Done")
