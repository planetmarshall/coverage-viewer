from view_coverage import load_coverage_data

import os
from pathlib import Path


def test_parse_coverage():
    root_dir = Path(os.path.realpath(os.path.join(os.path.dirname(__file__), "..")))
    file_tree = load_coverage_data(root_dir / 'test/data/example.json')

    tree = {
            "_filedata": [ {
                "filename": "main.cpp",
                "coverage": 100
            }],
            "lib": {
                "_filedata": [{
                "filename": "lib/library.cpp",
                    "coverage": 100
                }]
            }
        }

    assert file_tree == tree
