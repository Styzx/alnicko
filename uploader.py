import os
import sys
from multiprocessing import Pool, current_process, Manager

import requests
from tqdm import tqdm

# test url
URL = 'https://httpbin.org/post'
MAX_PROCESSES = 12
TERMINATING_NUMBER = 10

class Uploader(object):

    def __init__(self, files_list, max_processes, queue):
        self._files_list = files_list
        self._max_processes = max_processes
        self._queue = queue
        self._url = URL
        self._processes = None
        self._result_list = []
        self._pool = None
        self._pbar = None

    def start(self):
        processes = []
        # Pool variant
        self._processes = processes
        pool = Pool(processes=self._max_processes)
        total_bytes = 0
        self._pbar = tqdm(total=len(self._files_list))
        for i, file in enumerate(self._files_list):
            total_bytes += os.stat(file).st_size
            pool.apply_async(poster, args=(self._url, file, self._queue), callback=self.log_result)
        self._pool = pool

    def is_active(self):
        self._pool.close()
        self._pool.join()
        self._pbar.close()
        pids = []
        for res in self._result_list:
            pids.append(res['pid'])
            print(res)
        print('Process ids: ', set(pids))

    def log_result(self, result):
        progress = self._queue.get()

        self._result_list.append({'file': progress.done, 'status_code': progress.error, 'time_elapsed': progress.total, 'pid': progress.pid})
        # print(progress.done, progress.error, progress.total)
        self._pbar.update(1)

        # Upload interruption example
        # if self._pbar.n == TERMINATING_NUMBER:
        #     self._pool.terminate()
        #     print('Terminated at item № %s' % TERMINATING_NUMBER)

def poster(url, file, queue):
    post_file = {'file': open(file, 'rb')}
    r2 = requests.post(url, files=post_file)
    curp = current_process().pid
    print('Process id: ', curp)
    print('File posted: ', file)
    print('Time elapsed: ', r2.elapsed.total_seconds())
    progress = Progress()
    progress.done = file
    progress.error = r2.status_code
    progress.total = r2.elapsed.total_seconds()
    progress.pid = curp
    queue.put(progress)
    return(progress)

class Progress(object):

    def __init__(self):
        self._done = None
        self._error = None
        self._total = None
        self._pid = None

    # getter
    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, input):
        self._error = input

    # getter
    @property
    def done(self):
        return self._done

    @done.setter
    def done(self, input):
        self._done = input

    # getter
    @property
    def total(self):
        return self._total

    @total.setter
    def total(self, input):
        self._total = input

    # getter
    @property
    def pid(self):
        return self._pid

    @pid.setter
    def pid(self, input):
        self._pid = input


def main():
    dirpath = os.path.dirname(os.path.abspath(__file__))
    files_list = []
    for dirname, dirnames, filenames in os.walk(dirpath + '/files'):
        files_list = [os.path.join(dirname, filename) for filename in filenames]

    m = Manager()
    q = m.Queue()
    uploader = Uploader(files_list, MAX_PROCESSES, q)
    uploader.start()
    uploader.is_active()


if __name__ == '__main__':
    sys.exit(main())