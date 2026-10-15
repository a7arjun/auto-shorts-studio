import unittest
from unittest.mock import patch
from shorts import drive_batch as d

class DriveBatchTests(unittest.TestCase):
    def test_no_drive_ids(self):
        with patch.dict("os.environ",{"GDRIVE_SOURCE_FILE_IDS":""}):
            with self.assertRaises(RuntimeError):d.ids()
    def test_two_drive_ids(self):
        with patch.dict("os.environ",{"GDRIVE_SOURCE_FILE_IDS":"a"*24+","+"b"*24}):
            self.assertEqual(len(d.ids()),2)
    def test_public_locked(self):
        state={"published":[],"private_tests":[],"reservations":[]}
        with patch.dict("os.environ",{"BOLLYWOOD_PUBLIC_ENABLED":"false"}):
            with self.assertRaises(RuntimeError):d.guard("public",state)
    def test_cap(self):
        state={"published":[{"movie_index":i%2} for i in range(30)],
               "private_tests":[],"reservations":[]}
        self.assertIsNone(d.pick(state))
    def test_balanced_movies(self):
        state={"published":[{"movie_index":0}],"private_tests":[],"reservations":[]}
        self.assertEqual(d.pick(state),1)
    def test_private_never_needs_release_variables(self):
        with patch.dict("os.environ",{},clear=True):
            d.guard("private",{"published":[],"private_tests":[],"reservations":[]})
if __name__=="__main__":unittest.main()
