import numpy as np
import vcfstats.instance


old_instance_init = vcfstats.instance.Instance.__init__


# Rather than storing each individual GQ value, store counts of each
# value to save memory. Need to move around the datacols order so the
# axes are handled correctly.
def new_instance_init(self, *args, **kwargs):
    result = old_instance_init(self, *args, **kwargs)
    self.bincount = np.zeros(2, dtype=np.intp)
    self.bincount_length = len(self.bincount)
    self.datacols = ["Count", self.datacols[0]]
    return result


vcfstats.instance.Instance.__init__ = new_instance_init


# Take advantage of the fact that we only have low integer values
# with -1 if the field doesn't exist, so we can use bincount for
# efficient storage of the histogram data.
def new_instance_iterate(self, variant, vcf):
    try:
        # This is the most often used path, so make it quick
        self.bincount += np.bincount(
            variant.gt_quals.astype(np.intp) + 1, minlength=self.bincount_length
        )
    except ValueError as e:
        # Probably due to a new high GQ value, so resize the array
        # and try again. This will happen only a few times per file,
        # so it can be slower.
        this_bincount = np.bincount(variant.gt_quals.astype(np.intp) + 1)
        new_bincount_length = len(this_bincount)
        if new_bincount_length <= self.bincount_length:
            # Maybe not the cause of the ValueError after all
            raise e
        self.bincount.resize(new_bincount_length)
        self.bincount_length = new_bincount_length
        self.bincount += this_bincount


vcfstats.instance.Instance.iterate = new_instance_iterate


old_instance_plot = vcfstats.instance.Instance.plot


# Convert the bincount back into a list of (count, value) pairs for plotting
def new_instance_plot(self, *args, **kwargs):
    self.data = list(
        (count, ix - 1) for ix, count in enumerate(self.bincount) if count > 0
    )
    result = old_instance_plot(self, *args, **kwargs)
    return result


vcfstats.instance.Instance.plot = new_instance_plot


# Force column plot for GQ histogram, so we can set the heights using
# the counts in CounterList, rather than collecting and storing a pile
# of individual values.
def new_get_plot_type(*args, **kwargs):
    return "col"


vcfstats.instance.get_plot_type = new_get_plot_type
