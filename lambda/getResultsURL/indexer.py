from typing import Dict
import bisect


def _search(
    index: Dict[str, Dict[str, int]], chromosome: str, position: int
) -> int:
    """Finds the index entry where `position` falls in the chromosome index."""
    index_entry = index.get(chromosome, None)
    # Chromosome not found just return 0 (first page)
    if not index_entry:
        return 0

    chromosome_starts = index_entry["chromosome_start"]
    chromosome_ends = index_entry["chromosome_end"]

    # binary search
    idx = bisect.bisect_right(chromosome_starts, position) - 1

    if (
        0 <= idx < len(chromosome_ends)
        and chromosome_starts[idx] <= position <= chromosome_ends[idx]
    ):
        return idx

    # return last page - position is greater than last page
    return -1


def search_index_entry(
    index: Dict[str, Dict[str, int]], chromosome: str, position: int
) -> Dict[str, int]:
    """Returns the index entry for the given chromosome and position."""
    idx = _search(index, chromosome, position)

    return {
        "page": idx + 1,
        "page_start_f": index[chromosome]["page_start_f"][idx],
        "page_end_f": index[chromosome]["page_end_f"][idx],
        "chromosome_start": index[chromosome]["chromosome_start"][idx],
        "chromosome_end": index[chromosome]["chromosome_end"][idx],
    }


def get_index_page(index: Dict[str, Dict[str, int]], chromosome: str, page: int):
    idx = page - 1

    return {
        "page": page,
        "page_start_f": index[chromosome]["page_start_f"][idx],
        "page_end_f": index[chromosome]["page_end_f"][idx],
        "chromosome_start": index[chromosome]["chromosome_start"][idx],
        "chromosome_end": index[chromosome]["chromosome_end"][idx],
    }
