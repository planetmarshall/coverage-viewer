#! /usr/bin/env python

# view_coverage.py

# /// script
# dependencies = ["jq","pyside6"]
# ///

import os.path
import sys
from argparse import ArgumentParser
from math import floor
from typing import Tuple

from PySide6 import QtWidgets
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QTreeWidgetItem

from coverage_tools import FILE_DATA_KEY, load_coverage_data


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
            item.setText(1, f"{mean_coverage:.2f}")
            item.setBackground(2, self.color_from_coverage(mean_coverage))
            return item, mean_coverage

        for key in data.keys():
            if key != FILE_DATA_KEY:
                child_item, coverage = add_tree_node(None, key, data[key])
                root_items.append(child_item)

        self.tree.setColumnCount(3)
        self.tree.setHeaderLabels(["Name", "Coverage (pct)", "Heat Map"])
        self.tree.addTopLevelItems(root_items)


def main():
    parser = ArgumentParser(description="View coverage data for a source code tree")
    parser.add_argument("coverage_file", help="a json file generated from the llvm-cov tool")
    args = parser.parse_args()

    coverage_data = load_coverage_data(args.coverage_file)

    app = QtWidgets.QApplication([])

    widget = CoverageView()
    widget.setWindowTitle("Coverage Viewer")
    widget.set_data(coverage_data)
    widget.resize(1027, 768)
    widget.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
