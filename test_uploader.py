import os
import unittest
from multiprocessing import Manager

from uploader import Uploader


class TestSample(unittest.TestCase):

    def test_multiproc(self):
        processes_number = 12
        dirpath = os.path.dirname(os.path.abspath(__file__))
        files_list = []
        for dirname, dirnames, filenames in os.walk(dirpath + '/files'):
            files_list = [os.path.join(dirname, filename) for filename in filenames]
        m = Manager()
        q = m.Queue()
        uploader = Uploader(files_list, processes_number, q)
        uploader.start()
        uploader.is_active()
        pids = [res['pid'] for res in uploader._result_list]
        assert(len(set(pids)) == processes_number)