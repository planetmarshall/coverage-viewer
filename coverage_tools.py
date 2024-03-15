import itertools
import os
from fnmatch import fnmatch
from typing import List

import jq
from pathlib import Path

FILE_DATA_KEY = "_filedata"


def load_coverage_data(filename: Path) -> dict:
    with open(filename, "r") as fp:
        preprocessed_data = jq.compile(
            ".data.[0].files.[] | {filename: .filename, coverage: .summary.lines.percent}"
        ).input_text(fp.read())
        return parse_coverage_data(preprocessed_data)


def parse_coverage_data(coverage_data: dict, exclude_pattern: str | None = None) -> dict:
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
