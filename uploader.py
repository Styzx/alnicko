import sys
import os
import requests
from pathlib import Path
import time
from multiprocessing import Pool, Process, Queue, current_process
from multiprocessing.dummy import Pool as ThreadPool
import tqdm

# test url
URL = 'https://httpbin.org/post'
MAX_PROCESSES = 12

class Uploader(object):

    def __init__(self, files_list, max_processes, queue):
        # Process.__init__(self)
        # super(Uploader, self).__init__()
        self._files_list = files_list
        self._max_processes = max_processes
        self._queue = queue
        self._url = URL
        self._processes = None

    def start(self):
        # Process.start(self)
        # self._queue.put('something at %s' % time.time())
        processes = []
        pr = Progress()
        # pr.error = self.pid
        pr.done = current_process().name
        pr.error = current_process().pid
        self._queue.put(pr)
        print(pr.done)

        for file in self._files_list:
            proc = Process(target=poster, args=(self._url, file))
            processes.append(proc)
            proc.start()
        self._processes = processes
        # msg = self._queue.get()
        # print('Message: ', msg)

    def quit(self):
        self._queue.put('quit')

    def is_active(self):

        return self._processes[0].is_alive()
        # return True


def poster(url, file):
    post_file = {'file': open(file, 'rb')}
    print('File to post: ', post_file)
    r2 = requests.post(url, files=post_file)
    print('Time elapsed: ', r2.elapsed)


class Progress(object):

    def __init__(self):
        self._done = None
        self._error = None
        self.total = None

    # getter
    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, pid):
        self._error = pid

    # getter
    @property
    def done(self):
        return self._done

    @done.setter
    def done(self, pid):
        self._done = pid


def main():
    # sample = 'http://localhost:8080/sample.txt'
    # r = requests.get(sample)
    # print(r.text)
    # r.close()

    # get filenames from folder files
    dirpath = os.path.dirname(os.path.abspath(__file__))
    files_fullnames = []
    for dirname, dirnames, filenames in os.walk(dirpath + '/files'):
        files_fullnames = [os.path.join(dirname, filename) for filename in filenames]


    files_list = files_fullnames
    q = Queue()
    uploader = Uploader(files_list, MAX_PROCESSES, q)
    uploader.start()

    while uploader.is_active():
        progress = q.get()
        print(progress.done, progress.error, progress.total)
        # uploader.join()
    # uploader.join()
    # TODO: WHERE TO USE JOIN() CORRECTLY ????
    # uploader.terminate()


if __name__ == '__main__':
    sys.exit(main())