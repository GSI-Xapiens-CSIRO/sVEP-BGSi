from collections import Counter, defaultdict
import math

import plotnine as p9
from vcfstats.instance import Instance


BIN_WIDTH = 0.01
MAX_SAMPLES = 1000


# This should show a violin plot of allele frequencies, which will have
# a very small number of values, probably 0.5 and 1.0, and maybe 0.0.
# With a large number of variants, this uses a lot of memory, despite
# not needing the additional precision. Reduce the data points so the
# ratios remain the same but the memory usage is reduced.
old_instance_plot = Instance.plot


def new_instance_plot(self, *args, **kwargs):
    contig_aafs = defaultdict(Counter)
    for aaf, contig in self.data:
        contig_aafs[contig][aaf] += 1
    for contig, aaf_counts in contig_aafs.items():
        total = aaf_counts.total()
        if total > MAX_SAMPLES:
            multiplier = MAX_SAMPLES / total
            contig_aafs[contig] = Counter(
                {aaf: math.ceil(num * multiplier) for aaf, num in aaf_counts.items()}
            )
    self.data = [
        (aaf, contig)
        for contig, aaf_counts in contig_aafs.items()
        for aaf in aaf_counts.elements()
    ]
    return old_instance_plot(self, *args, **kwargs)


Instance.plot = new_instance_plot

# vcfstats doesn't provide an option to set the binwidth for violin plots,
# So we're going to jam it in here if it isn't already set.
old_p9_geom_violin = p9.geom_violin


def new_p9_geom_violin(*args, **kwargs):
    kwargs["bw"] = kwargs.get("bw", BIN_WIDTH)
    return old_p9_geom_violin(*args, **kwargs)


p9.geom_violin = new_p9_geom_violin
