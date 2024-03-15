#! /usr/bin/env python
from fnmatch import fnmatch
import itertools
import os.path
import sys
from argparse import ArgumentParser
import json
from pathlib import Path
from typing import List, Tuple

import jq
from PySide6 import QtCore, QtWidgets, QtCore
from PySide6.QtWidgets import QTreeWidgetItem

FILE_DATA_KEY = "_filedata"

class CoverageView(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.tree = QtWidgets.QTreeWidget()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.tree)

    def set_data(self, data: dict):
        root_items = []

        def add_tree_node(parent: QTreeWidgetItem | None, key, node: dict) -> Tuple[QTreeWidgetItem, float]:
            item = QTreeWidgetItem(parent)
            item.setText(0, key)
            sum_coverage = 0
            for subkey in node.keys():
                if subkey != "_filedata":
                    child, coverage = add_tree_node(item, subkey, node[subkey])
                    item.addChild(child)
                else:
                    sum_coverage = 0
                    n = 0
                    for filedata in node[FILE_DATA_KEY]:
                        sum_coverage += filedata["coverage"]
                        n += 1
                        file_item = QTreeWidgetItem(item)
                        file_item.setText(0, os.path.basename(filedata["filename"]))
                        file_item.setText(1, f"{filedata['coverage']:.2f}")
                        item.addChild(file_item)
                    coverage = sum_coverage / n

            item.setText(1, f"{coverage:.2f}")
            return item, coverage

        for key in data.keys():
            if key != FILE_DATA_KEY:
                child_item, coverage = add_tree_node(None, key, data[key])
                root_items.append(child_item)

        self.tree.setColumnCount(2)
        self.tree.setHeaderLabels(["Name", "Coverage (pct)"])
        self.tree.addTopLevelItems(root_items)

def load_coverage_data(filename: Path) -> dict:
    with open(filename, "r") as fp:
        preprocessed_data = jq.compile(
            ".data.[0].files.[] | {filename: .filename, coverage: .summary.lines.percent}"
        ).input_text(fp.read())
        return parse_coverage_data(preprocessed_data)

def parse_coverage_data(coverage_data: dict, exclude_pattern : str | None = None) -> dict:

    def _prefilter_filenames(files):
        for data in files:
            filename = data["filename"]
            if not exclude_pattern or not fnmatch(filename, exclude_pattern):
                yield data
            else:
                continue

    def set_node_filelist(data: dict, path: Path, cov_data: List[dict]):
        node = data
        for part in path.parts:
            if part not in node:
                node[part] = {}
            node = node[part]
        node[FILE_DATA_KEY] = cov_data

    data = list(_prefilter_filenames(coverage_data))

    root = os.path.commonprefix([element["filename"] for element in data])

    def _sort_by_dirname(obj):
        return os.path.dirname(obj["filename"])

    for element in data:
        element["filename"] = element["filename"].removeprefix(root)

    sorted_data = sorted(data, key=_sort_by_dirname)
    tree = {}
    for folder, files in itertools.groupby(sorted_data, key=_sort_by_dirname):
        set_node_filelist(tree, Path(folder), list(files))

    return tree


def main():
    parser = ArgumentParser(description="View coverage data for a source code tree")
    parser.add_argument("coverage_file", help="a json file generated from the llvm-cov tool")
    args = parser.parse_args()

    coverage_data = load_coverage_data(args.coverage_file)

    app = QtWidgets.QApplication([])

    widget = CoverageView()
    widget.setWindowTitle("Coverage Viewer")
    widget.set_data(coverage_data)
    widget.resize(800, 600)
    widget.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
