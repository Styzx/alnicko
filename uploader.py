import os
import sys
from multiprocessing import Pool, Process, current_process
from queue import Queue

import requests
from tqdm import tqdm

# test url
URL = 'https://httpbin.org/post'
MAX_PROCESSES = 4

class Uploader(object):

    def __init__(self, files_list, max_processes, queue):
        self._files_list = files_list
        self._max_processes = max_processes
        self._queue = queue
        self._url = URL
        self._processes = None
        self._result_list = []

    def start(self):
        processes = []
        pr = Progress()
        # pr.error = self.pid
        pr.done = current_process().name
        pr.error = current_process().pid

        # Pool variant
        self._processes = processes
        pool = Pool(processes=self._max_processes)
        total_bytes = 0
        for file in self._files_list:
            total_bytes += os.stat(file).st_size
            pool.apply_async(poster, args=(self._url, file), callback = self.log_result)
        pool.close()
        pool.join()

        print(self._result_list)

    def build_worker_pool(self, queue, size):
        workers = []
        for _ in range(size):
            worker = Processor(queue)
            worker.start()
            workers.append(worker)
        return workers

    def quit(self):
        self._queue.put('quit')

    def is_active(self):
        # workers = self.build_worker_pool(self._queue, self._max_processes)
        # self._processes = workers
        # for worker in workers:
        #     worker.join()
        for proc in self._processes:
            proc.join()
            proc.is_alive()

    def show_prog(self, q, total_bytes):
        prog = tqdm(total=total_bytes, desc="Total", unit='B', unit_scale=True)
        while 1:
            try:
                to_add = q.get(timeout=1)
                prog.n += to_add
                prog.update(0)
                if prog.n >= total_bytes:
                    break
            except:
                continue


    def log_result(self, result):
        # This is called whenever foo_pool(i) returns a result.
        # result_list is modified only by the main process, not the pool workers.
        self._result_list.append(result)


def poster(url, file):
    post_file = {'file': open(file, 'rb')}

    r2 = requests.post(url, files=post_file)
    print('Process id: ', current_process().pid)
    # queue.put(current_process().pid)
    print('File posted: ', post_file)
    print('Time elapsed: ', r2.elapsed.total_seconds())
    return {'file': file, 'status_code': r2.status_code, 'time_elapsed': r2.elapsed.total_seconds()}

class Processor(Process):

    def __init__(self, queue):
        super(Processor, self).__init__()
        self.file = queue.get()
        self.queue = queue
        self.url = URL

    def run(self):

        post_file = {'file': open(self.file, 'rb')}
        print('File to post: ', post_file)
        r2 = requests.post(self.url, files=post_file)
        print('Process id: ', current_process().pid)
        # queue.put(current_process().pid)
        print('Time elapsed: ', r2.elapsed.total_seconds())
        self.queue.put("Process idx={0} is called '{1}'".format(current_process().pid, self.name))
        # print("Process  idx={0} is called '{1}'".format(current_process().pid, self.name))
        # return {'file': self.file, 'status_code': r2.status_code, 'time_elapsed': r2.elapsed.total_seconds()}


class Progress(object):

    def __init__(self):
        self._done = None
        self._error = None
        self._total = None

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

    # getter
    @property
    def total(self):
        return self._total

    @total.setter
    def total(self, pid):
        self._total = pid


def main():
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


if __name__ == '__main__':
    sys.exit(main())