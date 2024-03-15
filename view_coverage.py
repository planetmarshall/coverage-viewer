#! /usr/bin/env python
from fnmatch import fnmatch
import itertools
import os.path
import sys
from argparse import ArgumentParser
from math import floor
from pathlib import Path
from typing import List, Tuple

import jq
from PySide6 import QtWidgets
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTreeWidgetItem

FILE_DATA_KEY = "_filedata"


class CoverageView(QtWidgets.QWidget):
    COLORS = [
        '#0c0786',
        '#40039c',
        '#6a00a7',
        '#8f0da3',
        '#b02a8f',
        '#cb4777',
        '#e06461',
        '#f2844b',
        '#fca635',
        '#fcce25',
        '#eff821'
    ]

    def __init__(self):
        super().__init__()
        self.tree = QtWidgets.QTreeWidget()

        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.addWidget(self.tree)

    @staticmethod
    def color_from_coverage(coverage):
        def clamp(x, min, max):
            return min if x < min else max if x > max else x
        index = clamp(floor(coverage * 0.1), 0, 10)
        return QColor(CoverageView.COLORS[index])

    def set_data(self, data: dict):
        root_items = []

        def add_tree_node(parent: QTreeWidgetItem | None, key, node: dict) -> Tuple[QTreeWidgetItem, float]:
            item = QTreeWidgetItem(parent)
            item.setText(0, key)
            sum_coverage = 0
            for subkey in node.keys():
                if subkey != FILE_DATA_KEY:
                    child, coverage = add_tree_node(item, subkey, node[subkey])
                    sum_coverage += coverage
                    item.addChild(child)
                else:
                    n = 0
                    for filedata in node[FILE_DATA_KEY]:
                        coverage = filedata["coverage"]
                        sum_coverage += coverage
                        n += 1
                        file_item = QTreeWidgetItem(item)
                        file_item.setText(0, os.path.basename(filedata["filename"]))
                        file_item.setText(1, f"{coverage:.2f}")
                        file_item.setBackground(2, self.color_from_coverage(coverage))
                        item.addChild(file_item)

            mean_coverage = sum_coverage / item.childCount()
            item.setText(1, f"{mean_coverage :.2f}")
            item.setBackground(2, self.color_from_coverage(mean_coverage))
            return item, mean_coverage

        for key in data.keys():
            if key != FILE_DATA_KEY:
                child_item, coverage = add_tree_node(None, key, data[key])
                root_items.append(child_item)

        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Name", "Coverage (pct)", "Heat Map"])
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
