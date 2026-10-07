import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).parents[1]/"skills/seedance-2-0/scripts"))
from seedance_job import build
class T(unittest.TestCase):
 def test_variants(self): self.assertEqual(build("seedance-2.0-mini","x")["model"],"seedance-2.0-mini")
 def test_reject(self):
  with self.assertRaises(ValueError): build("bad","x")
if __name__=="__main__":unittest.main()
