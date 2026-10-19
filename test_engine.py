import unittest
from engine import normalize_url, command

class SelectionTests(unittest.TestCase):
    URL = 'https://www.youtube.com/watch?v=vSw1qwplQmk&list=OLAK5uy_mta5EnM3CilF5owXXq61VUwiZWE1KS0Zk&index=22'

    def test_single_removes_playlist(self):
        self.assertEqual(normalize_url(self.URL), 'https://www.youtube.com/watch?v=vSw1qwplQmk')

    def test_playlist_starts_at_beginning(self):
        self.assertEqual(normalize_url(self.URL, True), 'https://www.youtube.com/playlist?list=OLAK5uy_mta5EnM3CilF5owXXq61VUwiZWE1KS0Zk')

    def test_invalid_hosts_and_modes(self):
        for value in ['file:///etc/passwd', 'https://youtube.com.evil.test/watch?v=abc', '--exec anything']:
            with self.assertRaises(ValueError):
                normalize_url(value)
        with self.assertRaises(ValueError):
            normalize_url('https://youtu.be/abc', True)

    def test_short_link(self):
        self.assertEqual(normalize_url('https://youtu.be/abc?t=3'), 'https://www.youtube.com/watch?v=abc')

    def test_output_quality_and_safe_arguments(self):
        args = command(self.URL, 'C:/음악 폴더', False)
        self.assertIn('320K', args)
        self.assertIn('--no-overwrites', args)
        self.assertEqual(args[-2], '--')
        self.assertNotIn('list=', args[-1])

if __name__ == '__main__':
    unittest.main()
