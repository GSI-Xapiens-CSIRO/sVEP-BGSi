from collections import defaultdict
import io
from typing import Dict, List


def create_index(file: io.BytesIO) -> Dict[str, Dict[str, List]]:
    max_lines_per_page = 1_000
    max_size_per_page = 10 * 10**6
    index = defaultdict(lambda: defaultdict(list))
    lines_read = 0
    size_read = 0
    page_start_f = 0
    page_start_pos = None
    previous_line = None
    previous_chrom = None
    previous_end = None

    while line := file.readline():
        # skip empty lines - TODO investigate and see why this happens
        if len(line.strip()) == 0:
            continue

        start = line.split(b"\t")[2]
        chrom, start_end = start.split(b":")
        start, end = [int(pos) for pos in start_end.split(b"-")]

        # first ever iteration
        if page_start_pos is None:
            page_start_pos = start
            previous_chrom = chrom

        # chrom changed
        if previous_chrom != chrom:
            # record last index entry of previous chromosome
            index[previous_chrom.decode()]["page_start_f"].append(page_start_f)
            index[previous_chrom.decode()]["page_end_f"].append(file.tell() - len(line))
            index[previous_chrom.decode()]["chromosome_start"].append(page_start_pos)
            index[previous_chrom.decode()]["chromosome_end"].append(previous_end)

            # reset
            page_start_pos = start
            page_start_f = file.tell() - len(line)
            lines_read = 0
            size_read = 0

        # last line of page has met
        if lines_read >= max_lines_per_page or size_read >= max_size_per_page:
            # add index entry
            index[chrom.decode()]["page_start_f"].append(page_start_f)
            index[chrom.decode()]["page_end_f"].append(file.tell())
            index[chrom.decode()]["chromosome_start"].append(page_start_pos)
            index[chrom.decode()]["chromosome_end"].append(end)

            # reset index to start at current line
            page_start_pos = start
            page_start_f = file.tell()
            lines_read = 0
            size_read = 0

        previous_chrom = chrom
        previous_end = end
        previous_line = line
        lines_read += 1
        size_read += len(line)

    # last index entry
    if previous_line:
        start = previous_line.split(b"\t")[2]
        chrom, start_end = start.split(b":")
        start, end = [int(pos) for pos in start_end.split(b"-")]
        chrom = chrom.decode()

        # chrom not seen before or last line is not the last line of the index entry
        if (
            len(index[chrom]["page_start_f"]) == 0
            or index[chrom]["page_start_f"][-1] != page_start_f
        ):
            index[chrom]["page_start_f"].append(page_start_f)
            index[chrom]["page_end_f"].append(file.tell())
            index[chrom]["chromosome_start"].append(page_start_pos)
            index[chrom]["chromosome_end"].append(end)

    return index
