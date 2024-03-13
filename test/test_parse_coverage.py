from view_coverage import parse_coverage_data

import json
import os
from pathlib import Path

def load_data():
    root_dir = Path(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
    with open(root_dir / 'test/data/example.json', 'r') as fp:
        return json.load(fp)


def test_parse_coverage():
    data = load_data()
    file_tree = parse_coverage_data(data)

    tree = {
        "folder": "example",
        "files": "main.cpp",
        "subfolders": [{
            "folder": "lib",
            "files": ["library.cpp"]
        }]
    }

    assert file_tree == tree
