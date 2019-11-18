import os
import sys
from multiprocessing import Pool, current_process, Manager
from typing import List

import requests
from tqdm import tqdm

# test url
URL = 'https://httpbin.org/post'
MAX_PROCESSES = 12
TERMINATING_NUMBER = 7


class Uploader(object):

    def __init__(self, files_list: List[str], max_processes: int, queue):
        self._files_list = files_list
        self._max_processes = max_processes
        self._queue = queue
        self._url = URL
        self._processes = None
        self._result_list = []
        self._pool = None
        self._pbar = None
        self._terminating_number = TERMINATING_NUMBER

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
        print('Uploaded files %s/%s: ' % (len(self._result_list), len(self._files_list)))
        for res in self._result_list:
            pids.append(res['pid'])
            print(res)
        print('Process ids: ', set(pids))

    def log_result(self, result):
        progress = self._queue.get()

        self._result_list.append({'file': progress.done, 'status_code': progress.error, 'time_elapsed': progress.total, 'pid': progress.pid})
        # print(progress.done, progress.error, progress.total)
        self._pbar.update(1)
        self.interrupt(TERMINATING_NUMBER)

    def interrupt(self, terminating_number: int):
        # Upload interruption
        if self._pbar.n == terminating_number:
            self._pool.terminate()
            print('Terminated at item № %s' % terminating_number)
            upfiles_list = [res['file'] for res in self._result_list]
            left_files_list = [res for res in self._files_list if res not in upfiles_list]
            print('Files not uploaded - %s/%s: ' % (len(left_files_list), len(self._files_list)))
            for lfl in left_files_list:
                print(lfl)


def poster(url: str, file: str, queue):
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
    return progress


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
    def error(self, value):
        self._error = value

    # getter
    @property
    def done(self):
        return self._done

    @done.setter
    def done(self, value):
        self._done = value

    # getter
    @property
    def total(self):
        return self._total

    @total.setter
    def total(self, value):
        self._total = value

    # getter
    @property
    def pid(self):
        return self._pid

    @pid.setter
    def pid(self, value):
        self._pid = value


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
