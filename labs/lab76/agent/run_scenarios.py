"""Run the corrected offline negative/positive tests, not the superseded12case fixture."""
import unittest
from pathlib import Path
if __name__=='__main__':
 suite=unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent),pattern='test_verifier.py')
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 raise SystemExit(not result.wasSuccessful())
