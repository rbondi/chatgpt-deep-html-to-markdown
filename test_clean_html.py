# -----------------------------------------------------------------------------
# Test Script: test_clean_html.py
#
# Purpose:
# Unit tests for the `clean_html` function defined in `clean_html.py`.
# This function is used to preprocess HTML files by removing unwanted elements
# (e.g. <svg> tags, empty divs) before converting to Markdown via Pandoc.
#
# This test suite verifies:
#   - That in-memory HTML strings are cleaned as expected.
#   - That real HTML files (golden inputs) produce the expected cleaned output.
# -----------------------------------------------------------------------------

import unittest
import tempfile
import os
from bs4 import BeautifulSoup
from clean_html import clean_html

class TestCleanHtml(unittest.TestCase):
    def setUp(self):
        # Set up in-memory test HTML and expected cleaned HTML output
        self.input_html = '''
        <html>
          <body>
            <div><svg><path d="M0 0h10v10H0z"/></svg></div>
            <div><p>   </p></div>
            <div><p>Hello World</p></div>
            <div><svg></svg><span></span></div>
          </body>
        </html>
        '''

        self.expected_output_html = '''
        <html>
          <body>
            <div><p>Hello World</p></div>
          </body>
        </html>
        '''

    # Normalize HTML strings by parsing and pretty-printing via BeautifulSoup
    # This helps ensure minor formatting differences don’t break tests
    def normalize_html(self, html_str):
        return BeautifulSoup(html_str, 'html.parser').prettify()

    # Test the clean_html function using in-memory file I/O (no disk fixtures)
    def test_clean_html_memory(self):
        with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.html') as infile:
            infile.write(self.input_html)
            infile.flush()
            input_path = infile.name

        with tempfile.NamedTemporaryFile(delete=False, mode='r+', suffix='.html') as outfile:
            output_path = outfile.name

        try:
            clean_html(input_path, output_path)
            with open(output_path, 'r', encoding='utf-8') as f:
                result = f.read()

            self.assertEqual(
                self.normalize_html(result),
                self.normalize_html(self.expected_output_html)
            )
        finally:
            os.remove(input_path)
            os.remove(output_path)

    # Test the clean_html function against golden input/output files
    def test_clean_html_with_file_io(self):
        input_path = os.path.join('testdata', 'golden_input.html')
        expected_path = os.path.join('testdata', 'golden_expected.html')

        with tempfile.NamedTemporaryFile(delete=False, mode='r+', suffix='.html') as outfile:
            output_path = outfile.name

        try:
            clean_html(input_path, output_path)

            with open(output_path, 'r', encoding='utf-8') as f:
                actual_output = f.read()
            with open('testdata/actual_output.html', 'w', encoding='utf-8') as f:
                f.write(actual_output)

            with open(expected_path, 'r', encoding='utf-8') as f:
                expected_output = f.read()

            self.assertEqual(
                self.normalize_html(actual_output),
                self.normalize_html(expected_output)
            )
        finally:
            os.remove(output_path)

# Run tests from the command line if executed directly
if __name__ == '__main__':
    unittest.main()