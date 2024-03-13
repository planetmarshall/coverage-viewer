#! /usr/bin/env python
import itertools
import os.path
import sys
import random
from argparse import ArgumentParser
import json
from pathlib import Path

from PySide6 import QtCore, QtWidgets, QtCore

class CoverageView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.tree = QtWidgets.QTreeWidget()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.tree)


def load_coverage_data(filename: Path) -> dict:
    with open(filename, "r") as fp:
        data = json.load(fp)

def parse_coverage_data(coverage_data: dict) -> dict:
    def set_node_filelist(data: dict, path: Path):
        pass

    files_data = coverage_data["data"][0]["files"]
    filenames = [ data["filename"] for data in files_data]
    root = os.path.commonprefix(filenames)
    sorted_filenames = sorted([Path(filename.removeprefix(root)) for filename in filenames])
    groups = []
    folders = []
    for folder, files in itertools.groupby(sorted_filenames, key=lambda filename: filename.parent):
        folders.append(folder)
        groups.append(list(files))

    pass


def main():
    parser = ArgumentParser(description="View coverage data for a source code tree")
    parser.add_argument("coverage-file", help="a json file generated from the llvm-cov tool")
    args = parser.parse_args()

    coverage_data = load_coverage_data(args.coverage_file)

    app = QtWidgets.QApplication([])

    widget = CoverageView()
    widget.setWindowTitle("Coverage Viewer")
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
