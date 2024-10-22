import unittest
from io import StringIO
import sys
import yaml
from virtual_shell import VirtualShell  

class TestVirtualShell(unittest.TestCase):
    def setUp(self):
        with open('config1.yaml', 'r') as f:
            config = yaml.safe_load(f)

        self.shell = VirtualShell(config) 

        with open('/tmp/testfile.txt', 'w') as f:
            f.write("line1\nline2\nline3\n")

    def tearDown(self):

        import os
        try:
            os.remove('/tmp/testfile.txt')
        except FileNotFoundError:
            pass 


    def test_ls(self):
        captured_output = StringIO()
        sys.stdout = captured_output
        self.shell.ls(['/'])
        sys.stdout = sys.__stdout__ 
        self.assertIn('/startup.sh', captured_output.getvalue())

    def test_cd(self):
        self.shell.cd(['/'])
        self.assertEqual(self.shell.current_path, '/')


    def test_cat(self):
        captured_output = StringIO()
        sys.stdout = captured_output
        self.shell.cat(['/tmp/testfile.txt']) 
        sys.stdout = sys.__stdout__
        self.assertIn('line1', captured_output.getvalue())
        self.assertIn('line2', captured_output.getvalue())
        self.assertIn('line3', captured_output.getvalue())

    def test_tail(self):
        captured_output = StringIO()
        sys.stdout = captured_output
        self.shell.tail(['/tmp/testfile.txt', '-n', '1'])
        sys.stdout = sys.__stdout__
        self.assertEqual(captured_output.getvalue().strip(), 'line3')

        captured_output = StringIO()
        sys.stdout = captured_output
        self.shell.tail(['/tmp/testfile.txt', '-n', '2']) 
        sys.stdout = sys.__stdout__
        self.assertIn('line2', captured_output.getvalue())
        self.assertIn('line3', captured_output.getvalue())


    def test_rmdir(self):
        import os
        os.makedirs('/tmp/testdir', exist_ok=True)
        self.assertTrue(os.path.exists('/tmp/testdir'))

        self.shell.rmdir(['/tmp/testdir'])
        self.assertFalse(os.path.exists('/tmp/testdir')) 


if __name__ == '__main__':
    unittest.main()