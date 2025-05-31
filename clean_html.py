#!/usr/bin/env python3
# clean_html.py
#
# This script takes an input HTML file and removes:
#   - All <svg> and <path> elements.
#   - Any ancestor <div> of a removed <svg> if that <div> becomes empty.
#   - All other <div> elements that contain no visible text or meaningful content.
#
# Usage:
#   python clean_html.py input.html output.html

import sys
from bs4 import BeautifulSoup

def has_text_or_non_svg(el):
    """
    Check whether the element or any of its descendants contain non-whitespace text
    or tags other than <svg> or <path>.
    """
    if el.name == 'svg' or el.name == 'path':
        return False

    # Check for text directly in the element
    if el.string and el.string.strip():
        return True

    # Check for any text or meaningful content in descendants
    for desc in el.descendants:
        if desc.name not in ['svg', 'path']:
            # If the descendant has text content that's not just whitespace
            if getattr(desc, 'string', None) and desc.string.strip():
                return True

    return False

def remove_empty_divs(soup):
    """
    Remove all <div> elements that contain no meaningful content (non-whitespace text
    or non-SVG/non-path children).
    """
    for div in soup.find_all('div'):
        if not has_text_or_non_svg(div):
            div.decompose()  # Delete the div if it's empty

def remove_svgs(soup):
    """
    Remove all <svg> elements, and also remove their parent <div> if it becomes empty
    after the SVG is removed.
    """
    for svg in soup.find_all('svg'):
        parent = svg.find_parent('div')  # Get the closest ancestor <div>
        svg.decompose()  # Remove the <svg> element

        # If the parent <div> is now empty of text or other content, remove it too
        if parent and not has_text_or_non_svg(parent):
            parent.decompose()

def clean_html(input_path, output_path):
    """
    Load HTML from input_path, clean it by removing <svg> elements and empty <div>s,
    and write the cleaned HTML to output_path.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'lxml')  # if you want to use lxml explicitly

    # First remove <svg> elements and possibly their empty parents
    remove_svgs(soup)

    # Then remove any other empty <div> elements
    remove_empty_divs(soup)

    # Write the cleaned HTML to output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(str(soup))

if __name__ == '__main__':
    # Ensure the script is called with exactly two arguments
    if len(sys.argv) != 3:
        print("Usage: python clean_html.py input.html output.html")
        sys.exit(1)

    # Get file paths from command-line arguments
    input_file = sys.argv[1]
    output_file = sys.argv[2]

    # Perform the cleaning operation
    clean_html(input_file, output_file)
