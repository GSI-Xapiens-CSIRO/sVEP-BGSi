=head1 LICENSE

Copyright [1999-2015] Wellcome Trust Sanger Institute and the EMBL-European Bioinformatics Institute
Copyright [2016-2019] EMBL-European Bioinformatics Institute

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file excepst in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

=cut


=head1 CONTACT

 Please email comments or questions to the public Ensembl
 developers list at <http://lists.ensembl.org/mailman/listinfo/dev>.

 Questions may also be sent to the Ensembl help desk at
 <http://www.ensembl.org/Help/Contact>.

=cut

=head1 NAME

Bio::EnsEMBL::Variation::Utils::VariationEffect

=head1 DESCRIPTION

This module defines a set of predicate subroutines that check the effect of a
Bio::EnsEMBL::Variation::VariationFeature on some other Bio::EnsEMBL::Feature.
All of these predicates take a VariationFeatureOverlapAllele as their first and
only argument and return a true or false value depending on whether the effect
being checked for holds or not. The link between these predicates and the
specific effect is configured in the Bio::EnsEMBL::Variation::Utils::Config
module and a list of OverlapConsequence objects that represent a link between,
for example, a Sequence Ontology consequence term, and the predicate that
checks for it is provided in the Bio::EnsEMBL::Variation::Utils::Constants
module. If you want to add a new consequence you should write a predicate in
this module and then add an entry in the configuration file.

=cut

package consequence::VariationEffect;

use strict;
use warnings;

use base qw(Exporter);
use Data::Dumper;
use consequence::CodonTable;
use consequence::Sequence qw(reverse_comp);
#use consequence::Sequence qw(reverse_comp);

our @EXPORT_OK = qw(overlap _intron_overlap within_feature within_cds MAX_DISTANCE_FROM_TRANSCRIPT within_intron stop_lost stop_retained start_lost frameshift $UPSTREAM_DISTANCE $DOWNSTREAM_DISTANCE);

use constant MAX_DISTANCE_FROM_TRANSCRIPT => 5000;

our $UPSTREAM_DISTANCE = MAX_DISTANCE_FROM_TRANSCRIPT;
our $DOWNSTREAM_DISTANCE = MAX_DISTANCE_FROM_TRANSCRIPT;

#
# Interface with some of the module function XS reimplementation
#
# If Bio::EnsEMBL::XS is installed, assign the function glob to
# the XS counterpart, otherwise assign to the original function
#
BEGIN {
  if (eval { require Bio::EnsEMBL::XS; 1 }) {
    *overlap = \&Bio::EnsEMBL::XS::Variation::Utils::VariationEffect::overlap;
  } else {
    *overlap = \&overlap_perl;
  }
}

# these two methods are perl implementations of the above Inline C
sub overlap_perl {
    my ( $f1_start, $f1_end, $f2_start, $f2_end ) = @_;

    return ( ($f1_end >= $f2_start) and ($f1_start <= $f2_end) );
}

sub _intron_overlap {
  my ($vf_start, $vf_end, $intron_start, $intron_end, $insertion) = @_;

  if(
   	overlap($vf_start, $vf_end, $intron_start+2, $intron_start+7) ||
   	overlap($vf_start, $vf_end, $intron_end-7,   $intron_end-2  ) ||
    overlap($vf_start, $vf_end, $intron_start-3, $intron_start-1) ||
   	overlap($vf_start, $vf_end, $intron_end+1,   $intron_end+3  ) ||
   	(
      $insertion && (
   	    $vf_start == $intron_start   ||
   	    $vf_end   == $intron_end     ||
   	    $vf_start == $intron_start+2 ||
   	    $vf_end   == $intron_end-2
      )
    )
  ) {
    return 1;
  }
  else {
    return 0;
  }
}

sub within_feature {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvf  ||= $bvfoa->base_variation_feature;
    $feat ||= $bvfoa->feature;

    return overlap(
        $bvf->{start},
        $bvf->{end},
        $feat->{start},
        $feat->{end}
    );
}

sub partial_overlap_feature {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvf  ||= $bvfoa->base_variation_feature;
    $feat ||= $bvfoa->feature;

    return (
        within_feature(@_) and
        (not complete_overlap_feature(@_)) and
        (($bvf->{end} > $feat->{end}) or ($bvf->{start} < $feat->{start}))
    );
}

sub complete_within_feature {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvf  ||= $bvfoa->base_variation_feature;
    $feat ||= $bvfoa->feature;

    return (
        ($bvf->{start} >= $feat->{start}) and
        ($bvf->{end} <= $feat->{end})
    );
}

sub complete_overlap_feature {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvf  ||= $bvfoa->base_variation_feature;
    $feat ||= $bvfoa->feature;

    return (
        ($bvf->{start} <= $feat->{start}) and
        ($bvf->{end} >= $feat->{end})
    );
}

sub deletion {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvf ||= $bvfoa->base_variation_feature;

    # sequence variant will have alleles
    if($bvf->isa('Bio::EnsEMBL::Variation::VariationFeature')) {
        my ($ref_allele, $alt_allele) = _get_alleles(@_);
        return (
            (defined($ref_allele) && ($alt_allele eq '' || length($alt_allele) < length($ref_allele)) and $ref_allele) or
            $bvf->allele_string =~ /deletion/i
        );
    }

    # structural variant depends on class
    if($bvf->isa('Bio::EnsEMBL::Variation::StructuralVariationFeature')) {
        return (
            ($bvf->class_SO_term(undef, 1) eq 'deletion') or
            ($bvf->class_SO_term(undef, 1) =~ /deletion/i) or
            ($bvf->class_SO_term(undef, 1) =~ /loss/i)
        );
    }

    else { return 0; }
}

sub insertion {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvf ||= $bvfoa->base_variation_feature;

    # sequence variant will have alleles
    if($bvf->isa('Bio::EnsEMBL::Variation::VariationFeature')) {
        my ($ref_allele, $alt_allele) = _get_alleles(@_);
        return (
            (defined($ref_allele) && ($ref_allele eq '' || length($alt_allele) > length($ref_allele)) and $alt_allele) or
            $bvf->allele_string =~ /insertion/i
        );
    }

    # structural variant depends on class
    if($bvf->isa('Bio::EnsEMBL::Variation::StructuralVariationFeature')) {
        return (
            duplication(@_) or
            tandem_duplication(@_) or
            ($bvf->class_SO_term(undef, 1) eq 'insertion') or
            ($bvf->class_SO_term(undef, 1) =~ /insertion/i) or
            ($bvf->class_SO_term(undef, 1) =~ /gain/i)
        );
    }

    else { return 0; }
}

sub copy_number_gain {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvf ||= $bvfoa->base_variation_feature;

    return (duplication(@_) or tandem_duplication(@_) or $bvf->class_SO_term(undef, 1) =~ /gain/i);
}

sub copy_number_loss {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvf ||= $bvfoa->base_variation_feature;

    return $bvf->class_SO_term(undef, 1) =~ /loss/i;
}

sub duplication {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvf ||= $bvfoa->base_variation_feature;

    return (
        (
            ($bvf->class_SO_term(undef, 1) eq 'duplication') or
            ($bvf->class_SO_term(undef, 1) =~ /duplication/i)
        ) and
        (not tandem_duplication(@_))
    );
}

sub tandem_duplication {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvf ||= $bvfoa->base_variation_feature;

    # for sequence variants, check sequence vs ref
    if($bvf->isa('Bio::EnsEMBL::Variation::VariationFeature')) {
        my ($ref_allele, $alt_allele) = _get_alleles(@_);

        return 0 unless $ref_allele and $alt_allele;
        return 0 unless
            length($alt_allele) > length($ref_allele) and
            length($alt_allele) % length($ref_allele) == 0;

        my $copies = length($alt_allele) / length($ref_allele);

        return $alt_allele eq $ref_allele x $copies;
    }

    # structural variant depends on class
    if($bvf->isa('Bio::EnsEMBL::Variation::StructuralVariationFeature')) {
        return (
            ($bvf->class_SO_term(undef, 1) eq 'tandem_duplication') or
            ($bvf->class_SO_term(undef, 1) =~ /tandem_duplication/i)
        );
    }
}

sub feature_ablation {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $feat ||= $bvfoa->base_variation_feature_overlap->feature;

    return (complete_overlap_feature($bvfoa, $feat, $bvfo, $bvf) and deletion(@_));
}

sub feature_amplification {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $feat ||= $bvfoa->base_variation_feature_overlap->feature;

    return (complete_overlap_feature($bvfoa, $feat, $bvfo, $bvf) and copy_number_gain(@_));
}

sub feature_elongation {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $feat ||= $bvfoa->base_variation_feature_overlap->feature;

    return 0 if $bvfoa->isa('Bio::EnsEMBL::Variation::TranscriptVariationAllele');

    return (
        complete_within_feature($bvfoa, $feat, $bvfo, $bvf) and
        (copy_number_gain(@_) or insertion(@_))
    );
}

sub feature_truncation {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $feat ||= $bvfoa->base_variation_feature_overlap->feature;

    return 0 if $bvfoa->isa('Bio::EnsEMBL::Variation::TranscriptVariationAllele');

    return (
        (
            partial_overlap_feature($bvfoa, $feat, $bvfo, $bvf) or
            complete_within_feature($bvfoa, $feat, $bvfo, $bvf)
        ) and
        (
            copy_number_loss(@_) or deletion(@_)
        )
    );
}

sub protein_altering_variant{

    ## check in protein
    my ($ref_pep, $alt_pep) = _get_peptide_alleles(@_);
    #print("\nprotein_altering_variant\n");

    return 0 unless defined $ref_pep && defined $alt_pep;

    ## don't assign if child term appropriate

    return 0 if  length($alt_pep) eq length($ref_pep);       # synonymous_variant(@_);  missense_variant(@_);
    return 0 if  $ref_pep =~/^\*/  || $alt_pep =~/^\*/;      # stop lost/ gained/ retained
    return 0 if  $alt_pep =~/^\Q$ref_pep\E|\Q$ref_pep\E$/;   # inframe_insertion(@_);

    return 0 if inframe_deletion(@_);
    return 0 if start_lost(@_);
    return 0 if frameshift(@_);

    return 1;
}

#sub transcript_fusion {
#    #my ($bvfoa, $feat, $bvfo, $bvf) = @_;
#    #my $bvf   = $bvfoa->base_variation_feature;
#
#    return 0;
#
#    #my $transcripts = $bvf->_get_overlapping_Transcripts();
#}

sub _before_start {
    my ($bvf, $feat, $dist) = @_;

    return ( ($bvf->{end} >= ($feat->{start} - $dist)) and
        ($bvf->{end} < $feat->{start}) );
}

sub _after_end {
    my ($bvf, $feat, $dist) = @_;
    return ( ($bvf->{start} <= ($feat->{end} + $dist))
            and ($bvf->{start} > $feat->{end}) );
}

sub _upstream {
    my ($bvf, $feat, $dist) = @_;
    return $feat->strand == 1 ?
        _before_start($bvf, $feat, $dist) :
        _after_end($bvf, $feat, $dist);
}

sub _downstream {
    my ($bvf, $feat, $dist) = @_;
    return $feat->strand == 1 ?
        _after_end($bvf, $feat, $dist) :
        _before_start($bvf, $feat, $dist);
}

#package Bio::EnsEMBL::Variation::TranscriptVariationAllele;

sub upstream {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvf  ||= $bvfoa->base_variation_feature;
    $feat ||= $bvfoa->base_variation_feature_overlap->feature;

    return _upstream($bvf, $feat, $UPSTREAM_DISTANCE);
}

sub downstream {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvf  ||= $bvfoa->base_variation_feature;
    $feat ||= $bvfoa->base_variation_feature_overlap->feature;

    return _downstream($bvf, $feat, $DOWNSTREAM_DISTANCE);
}

sub affects_transcript {
    my ($bvf, $tran) = @_;

    return 0 unless $tran->isa('Bio::EnsEMBL::Transcript');

    return overlap(
        $bvf->{start},
        $bvf->{end},
        $tran->{start} - 5000,
        $tran->{end} + 5000
    );
}

sub within_transcript {
    return within_feature(@_);
}

sub within_nmd_transcript {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $feat ||= $bvfoa->base_variation_feature_overlap->feature;

    return ( within_transcript(@_) and ($feat->{biotype} eq 'nonsense_mediated_decay') );
}

sub within_non_coding_gene {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $feat ||= $bvfoa->base_variation_feature_overlap->feature;

    return ( within_transcript(@_) and (not $feat->translation) and (not within_mature_miRNA(@_)) and (not non_coding_exon_variant(@_)) );
}

sub non_coding_exon_variant {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;

    return 0 if $feat->translation or within_mature_miRNA(@_);

    # get overlapped exons
    # this may include some non-overlapping ones in the case of transcripts with frameshift introns
    # so we double check with overlap()
    #print Dumper $bvfo;
    #print($feat->{cdna_coding_start});
    #my $exons = $bvfo->_overlapped_exons;

    if(length $feat->{exon_start} ) {
      if(overlap($bvf->{start}, $bvf->{end}, $feat->{exon_start}, $feat->{exon_end})) {
        return 1;
      }
      else {
        return 0;
      }
    }else{
      return 0;
    }
}

sub within_miRNA {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;

    # don't call this for now

    return 0;
    $feat ||= $bvfoa->base_variation_feature_overlap->feature;

    return ( ($feat->biotype eq 'miRNA') and within_transcript(@_) );
}

sub within_mature_miRNA {
  my ($bvfoa, $feat, $bvfo, $bvf) = @_;
  $bvfo ||= $bvfoa->base_variation_feature_overlap;
  $bvf  ||= $bvfo->base_variation_feature;
  $feat ||= $bvfo->feature;

  return 1 if ( ($feat->{biotype} eq 'miRNA') and within_transcript(@_) and $feat->{within_mirna} == 1  );

  #foreach my $attribute(@{ $feat->get_all_Attributes('miRNA') }) {

  #  if (defined $attribute && $attribute->value =~ /(\d+)-(\d+)/) {
  #    for my $coord ($bvfo->_mapper->cdna2genomic($1, $2)) {
  #      if ($coord->isa('Bio::EnsEMBL::Mapper::Coordinate')) {
  #        if (overlap(
  #            $bvf->seq_region_start(),
  #            $bvf->seq_region_end(),
  #            $coord->start,
  #            $coord->end) ) {
  #          return 1;
  #        }
  #      }
  #    }
  #  }
  #}

  return 0;
}

sub donor_splice_site {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;
    $feat ||= $bvfo->feature;

    my $cache = $bvfoa->{_predicate_cache} ||= {};
    #unless(exists($cache->{splice_donor_variant})) {
    #    $cache->{splice_donor_variant} = 0;
        if(length $feat->{'splice_donor_variant'}){ #$feat->{'three_prime_utr'} == 1 &&
          return $cache->{splice_donor_variant} = 1 if ( $feat->{'intron_boundary'} == 1 && $feat->{'splice_donor_variant'} ==1);
        }
    #  }

    #print("\nsplice regions = ", $cache->{splice_donor_variant},"\n");
    #return $cache->{splice_donor_variant};
    return 0;
}

sub acceptor_splice_site {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;
    $feat ||= $bvfo->feature;
    my $cache = $bvfoa->{_predicate_cache} ||= {};
    #unless(exists($cache->{splice_acceptor_variant})) {
    #  $cache->{splice_acceptor_variant} = 0;
      if(length $feat->{'splice_acceptor_variant'}){ #$feat->{'three_prime_utr'} == 1 &&
        return $cache->{splice_acceptor_variant} = 1 if ( $feat->{'intron_boundary'} == 1 && $feat->{'splice_acceptor_variant'} ==1);
      }
    #}

    #return $cache->{splice_acceptor_variant};
    return 0;
}

sub essential_splice_site {
    return ( acceptor_splice_site(@_) or donor_splice_site(@_) );
}

sub splice_region {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;
    my $cache = $bvfoa->{_predicate_cache} ||= {};
    unless(exists($cache->{splice_region_variant})) {
      $cache->{splice_region_variant} = 0;

      return 0 if donor_splice_site(@_);
      return 0 if acceptor_splice_site(@_);
      return 0 if essential_splice_site(@_);
    #return $bvfoa->_intron_effects($feat, $bvfo, $bvf)->{splice_region};
      if(length $feat->{'splice_region_variant'}){
        if ($feat->{'intron_boundary'} == 1 && $feat->{'splice_region_variant'} == 1){
          $cache->{splice_region_variant} = 1;
        }
      }
    }

    return $cache->{splice_region_variant};
}

sub within_intron {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;

    return 1 if exists($bvf->{'intron'}) && $bvf->{'intron'} ==1;
    #return $bvfoa->_intron_effects($feat, $bvfo, $bvf)->{intronic};
}

sub within_cds {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;
    $feat ||= $bvfo->feature;
    $bvf  ||= $bvfo->base_variation_feature;

    my $cds_coords = $bvfo->cds_coords;

    if (@$cds_coords > 0) {
        for my $coord (@$cds_coords) {
            if ($coord->isa('Bio::EnsEMBL::Mapper::Coordinate')) {
                if ($coord->end > 0 && $coord->start <= length($bvfo->_translateable_seq)) {
                    return 1;
                }
            }
        }
    }

    # we also need to check if the vf is in a frameshift intron within the CDS

    if (defined $feat->translation &&
        $bvfoa->_intron_effects($feat, $bvfo, $bvf)->{within_frameshift_intron}) {

        return overlap(
            $bvf->{start},
            $bvf->{end},
            $feat->coding_region_start,
            $feat->coding_region_end,
        );
    }

    return 0;
}

sub within_cdna {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;
    $feat ||= $bvfo->feature;

    my $cdna_coords = $bvfo->cdna_coords;

    if (@$cdna_coords > 0) {
        for my $coord (@$cdna_coords) {
            if ($coord->isa('Bio::EnsEMBL::Mapper::Coordinate')) {
                if ($coord->end > 0 && $coord->start <= $feat->length) {
                    return 1;
                }
            }
        }
    }

    # we also need to check if the vf is in a frameshift intron within the cDNA

    if ($bvfoa->_intron_effects->{within_frameshift_intron}) {
        return within_transcript(@_);
    }

    return 0;
}

sub _before_coding {
    my ($bvf, $tran) = @_;
    return 0 unless defined $tran->translation;

    my $bvf_s  = $bvf->{start};
    my $bvf_e  = $bvf->{end};
    my $t_s    = $tran->{start};
    my $cds_s  = $tran->coding_region_start;

    # we need to special case insertions just before the CDS start
    if ($bvf_s == $bvf_e+1 && $bvf_s == $cds_s) {
        return 1;
    }

    return overlap($bvf_s, $bvf_e, $t_s, $cds_s-1);
}

sub _after_coding {
    my ($bvf, $tran) = @_;
    return 0 unless defined $tran->translation;

    my $bvf_s  = $bvf->{start};
    my $bvf_e  = $bvf->{end};
    my $t_e    = $tran->{end};
    my $cds_e  = $tran->coding_region_end;

    # we need to special case insertions just after the CDS end
    if ($bvf_s == $bvf_e+1 && $bvf_e == $cds_e) {
        return 1;
    }

    return overlap($bvf_s, $bvf_e, $cds_e+1, $t_e);
}

sub within_5_prime_utr {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;
    $feat ||= $bvfo->feature;
    $bvf  ||= $bvfo->base_variation_feature;

    my $five_prime_of_coding =
        $feat->strand == 1 ?
            _before_coding($bvf, $feat) :
            _after_coding($bvf, $feat);

    return ( $five_prime_of_coding and within_cdna(@_) );
}

sub within_3_prime_utr {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;
    $feat ||= $bvfo->feature;
    $bvf  ||= $bvfo->base_variation_feature;

    my $three_prime_of_coding =
        $feat->strand == 1 ?
            _after_coding($bvf, $feat) :
            _before_coding($bvf, $feat);

    return ( $three_prime_of_coding and within_cdna(@_) );
}

sub complex_indel {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;
    $bvf  ||= $bvfo->base_variation_feature;

    # pass the no_db flag to var_class to ensure we don't rely on the database for it
    # as it may not have been set at this stage in the pipeline
    my $class = $bvf->var_class(1);

    return 0 unless $class =~ /insertion|deletion|indel/;

    return @{ $bvfo->cds_coords } > 1;
}

sub get_adjacent_exon_nucleotides {
    my ($feat, $bvf, $earlier, $num_bases) = @_;
    my $chr = $bvf->{'chr'};
    my $fasta_file = $bvf->{'fasta_file'};
    my $gtf_file = $bvf->{'gtf_file'};
    my $reference_chr = $bvf->{'reference_chr'};
    my $transcript_start = $feat->{'start'};
    my $transcript_end = $feat->{'end'};
    my $transcript_id = $feat->{'stable_id'};
    my $cdna_start = $feat->{'cdna_coding_start'};
    my $cdna_end = $feat->{'cdna_coding_end'};
    my $position = $feat->{'position'};
    my $tabix_result = `./tabix $gtf_file $reference_chr:$transcript_start-$transcript_end`;
    my @cds_coords = ();
    my $exon_index = undef;
    for my $record (split /[\r\n]+/, $tabix_result){
        my @info = (split '\t', $record);
        if ($info[2] eq "CDS" && $info[7] eq $transcript_id){
            if ($info[3] eq $cdna_start && $info[4] eq $cdna_end){
                $exon_index = @cds_coords;
            }
            push @cds_coords, [$info[3], $info[4]];
        }
    }
    unless (defined $exon_index){
        print "CDS not found in gtf file searching $gtf_file for $reference_chr:$transcript_start-$transcript_end\n";
        $feat->{warning} = "CDS is not found in gtf file";
        print Dumper $feat;
        print Dumper $bvf;
        print "Just using As as a placeholder. This will be wrong, but at least it won't crash.\n";
        return "A" x $num_bases;
    }
    my ($query_start, $query_end) = undef;
    if ($earlier){
        my $prev_end_coords = $cds_coords[$exon_index-1][1];
        ($query_start, $query_end) = ($prev_end_coords+1-$num_bases, $prev_end_coords);
    } else {
        my $next_start_coords = $cds_coords[$exon_index+1][0];
        ($query_start, $query_end) = ($next_start_coords, $next_start_coords-1+$num_bases);
    }
    my $faidx_result = `./samtools faidx $fasta_file $reference_chr:$query_start-$query_end`;
    my @faidx_lines = split(/\n/, $faidx_result);
    return $faidx_lines[1];
}

sub _get_peptide_alleles {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    my $cache = $bvfoa->{_predicate_cache} ||= {};
    my @alleles = ();
    my $ref_seq = $feat->{'seq'};

    my $ref_allele = $feat->{'ref_allele'};
    my $alt_allele = $feat->{'alt_allele'};
    my $frame = $feat->{'cds_frame'};  # This should be between 0 and 2
    my $var_loc =  $feat->{'position'} - $feat->{'cdna_coding_start'};
    my $var_loc_end = $var_loc + length($ref_allele) - 1;
    my $strand = $feat->{'strand'};

    my $seq_length = $feat->{'seq_length'};
    # Handle the case of deletions that span the end of the CDS
    # The biological implications of this are uncertain,
    # So we'll treat as if transcription starts or ends earlier,
    # rather than going outside the CDS.
    # The main finding will be splice_region_variant
    if ($var_loc_end >= $seq_length) {
        # Deletion spans the end of the CDS
        my $new_ref_length = length($ref_allele) - $var_loc_end + $seq_length - 1;
        $ref_allele = substr($ref_allele, 0, $new_ref_length);
        $alt_allele = substr($alt_allele, 0, $new_ref_length);
        $var_loc_end = $seq_length - 1;
    }
    if ($var_loc < 0) {
        # Deletion starts before the start of the CDS
        my $new_ref_length = length($ref_allele) + $var_loc;
        $ref_allele = substr($ref_allele, -$new_ref_length);
        $alt_allele = substr($alt_allele, -$new_ref_length);
        $var_loc = 0;
    }
    my $trailing_bases = ($seq_length - $frame) % 3;
    # subtracting the length to handle deletions, the -1 and +1 cancel out
    my $rev_var_loc = $seq_length - $var_loc_end - 1;
    if ($rev_var_loc < 0) {
        $rev_var_loc = 0;
    }
    my $pad_start = 0;
    my $pad_end = 0;
    my $reset_frame = 0;
    if ($strand == 1) {
        if ($var_loc < $frame) {
            # Need to look at previous exon to create codon
            $pad_start = 3 - $frame;
            $reset_frame = 1;
        }
        if ($rev_var_loc < $trailing_bases) {
            # Need to look at next exon to create codon
            $pad_end = 3 - $trailing_bases;
        }
    } else {
        if ($var_loc < $trailing_bases) {
            # Need to look at previous exon to create codon
            $pad_start = 3 - $trailing_bases;
        }
        if ($rev_var_loc < $frame) {
            # Need to look at next exon to create codon
            $pad_end = 3 - $frame;
            $reset_frame = 1;
        }
    }
    if ($pad_start) {
        $ref_seq = get_adjacent_exon_nucleotides($feat, $bvf, 1, $pad_start).$ref_seq;
        $var_loc += $pad_start;
        $var_loc_end += $pad_start;
    }
    if ($pad_end) {
        $ref_seq = $ref_seq.get_adjacent_exon_nucleotides($feat, $bvf, 0, $pad_end);
        $rev_var_loc += $pad_end;
    }
    if ($reset_frame) {
        $frame = 0;
    }
    $ref_seq = lc($ref_seq);
    my $alt_seq = $ref_seq;

    if($ref_seq =~ /^TGA$|^TAA$|^TAG$/i){#This is for stop retained variant where you want to check the original ref for stop
      #print("\nSTOP REFFFF - $ref_seq\n");
      $feat->{stop_ref} = $ref_seq;
      $feat->{stop_alt} = $ref_seq;
      substr($feat->{stop_alt}, $var_loc, length $alt_allele) = $alt_allele;
    }
    if(CORE::fc(substr($ref_seq, $var_loc, length $ref_allele)) =~ CORE::fc($ref_allele) ){
      substr($ref_seq, $var_loc, length $ref_allele) = $ref_allele;  # This is just to set it to uppercase
      substr($alt_seq, $var_loc, length $ref_allele) = $alt_allele;
    }elsif($ref_allele eq "-"){
      substr($alt_seq, $var_loc, 0) = $alt_allele;
    }elsif(CORE::fc(substr($ref_seq, $var_loc, length $ref_allele)) ne CORE::fc($ref_allele) || $alt_allele eq "-"){
      $feat->{warning} = "REF doesn't match GRCh38 reference at given position";
      substr($ref_seq, $var_loc, length $ref_allele) = $ref_allele;
      substr($alt_seq, $var_loc, length $ref_allele) = $alt_allele;
    }elsif($alt_allele eq "-"){
      substr($alt_seq, $var_loc, length $ref_allele) = $alt_allele;
    }else{
      $feat->{warning} = "REF doesn't match GRCh38 reference at given position";
      substr($ref_seq, $var_loc, length $ref_allele) = $ref_allele;
      substr($alt_seq, $var_loc, length $ref_allele) = $alt_allele;
    }
    if($strand == -1){
      reverse_comp(\$ref_seq);
      reverse_comp(\$alt_seq);
      $var_loc = $rev_var_loc;
      $var_loc_end = $var_loc + length($ref_allele) - 1;
    }
    my $codon_start = $frame + 3 * int(($var_loc-$frame) / 3);
    my $codon_end = $frame + 2 + 3 * int(($var_loc_end-$frame-2) / 3 + 0.9);  # who needs a ceil function?
    my $bases_to_trim = length($ref_seq) - $codon_end - 1;
    my $ref_pep_allele = substr($ref_seq, $codon_start, -$bases_to_trim || (length($ref_seq)-$codon_start));
    my $alt_pep_allele = substr($alt_seq, $codon_start, -$bases_to_trim || (length($alt_seq)-$codon_start));
    if($ref_pep_allele =~/^TGA$|^TAA$|^TAG$/i && $alt_pep_allele =~"-"){
      $alt_pep_allele = $ref_pep_allele;
    }
    $ref_seq =~ s/-//g;
    $alt_seq =~ s/-//g;
    $ref_pep_allele =~ s/-//g;
    $alt_pep_allele =~ s/-//g;
    if(length($ref_pep_allele) % 3 != 0){
      print("\nCodon is out of CDS range.\n");
      $feat->{warning} = "Codon is out of CDS range.";
    }

    my $ref_pep = translate($ref_seq,$frame);
    my $alt_pep = translate($alt_seq,$frame);


    if(!length $ref_pep_allele &&  !length $alt_pep_allele) {
      print("\nFailed!\n");
      $feat->{warning} = "Frame removes the variant position out of equation";
      $bvfo->{startRef} = substr($ref_seq, $frame, 3);
      $bvfo->{startAlt} = substr($alt_seq, $frame, 3);
      @alleles = ($ref_pep, $alt_pep);
      $cache->{_get_peptide_alleles} = \@alleles;
      return @{$cache->{_get_peptide_alleles}};
    }


    my $ref_aa = consequence::CodonTable->translate( $ref_pep_allele, 1);
    my $alt_aa = consequence::CodonTable->translate( $alt_pep_allele);
    if(length($alt_pep_allele) % 3 != 0){
      $alt_aa .='X';
    }
    #print("$ref_aa\n$alt_aa\n");
    #print("$ref_pep_allele\n$alt_pep_allele\n");
    #exit();

    @alleles = ($ref_pep, $alt_pep);
    $cache->{_get_peptide_alleles} = \@alleles;
    $feat->{altCodon} = uc($alt_pep_allele);
    $feat->{refCodon} = uc($ref_pep_allele);
    $feat->{altaa} = $ref_aa;
    $feat->{refaa} = $alt_aa;
    $feat->{codons} = ($ref_pep_allele||"-")."/".($alt_pep_allele||"-");
    $feat->{aa} = $ref_aa eq $alt_aa ? $ref_aa : ($ref_aa||"-")."/".($alt_aa||"-");

    $bvfo->{startRef} = uc(substr($ref_seq, $frame, 3));
    $bvfo->{startAlt} = uc(substr($alt_seq, $frame, 3));
    $feat->{_variation_effect_feature_cache}->{peptide} = $ref_pep;
    return @{$cache->{_get_peptide_alleles}};
}



sub translate {
  my ($mrna,$frame) = @_;


  # Alternative codon tables (such as the mitochondrial codon table)
  # can be specified for a sequence region via the seq_region_attrib
  # table.  A list of codon tables and their codes is at:
  # http://www.ncbi.nlm.nih.gov/Taxonomy/Utils/wprintgc.cgi

  my $codon_table_id;

  $codon_table_id ||= 1;    # default vertebrate codon table

  # Remove final stop codon from the mrna if it is present.  Produced
  # peptides will not have '*' at end.  If terminal stop codon is
  # desired call translatable_seq directly and produce a translation
  # from it.
  #print(CORE::length($mrna) % 3);
  #if ( CORE::length($mrna) % 3 == 0 ) {
    #print("HI");
    #print("\nAre We Here\n");
  #  my $codon_table = consequence::CodonTable->new( -id => $codon_table_id );

  #  if ( $codon_table->is_ter_codon( substr( $mrna, -3, 3 ) ) ) {
  #    substr( $mrna, -3, 3, '' );
  #  }
  #} #elsif ( CORE::length($mrna) % 3 == 2 ) {

	  # Otherwise trim those last two bp off so the behavior is
	  # consistent across bioperl versions
	  #substr( $mrna, -2, 2, '' );
  #}

  if ( CORE::length($mrna) < 1 ) { return undef }
  #print Dumper $codon_table;

  my $translation = consequence::CodonTable->translate( $mrna, 1,$frame);

  #print Dumper $translation;
  return $translation;

} ## end sub translate

sub _get_ref_pep {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;
    return $bvfo->get_reference_TranscriptVariationAllele->peptide;
}

sub _get_codon_alleles {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;

    return () if frameshift(@_);

    my $alt_codon = $feat->{altCodon};

    return () unless defined $alt_codon;

    $bvfo ||= $bvfoa->base_variation_feature_overlap;
    my $ref_codon = $feat->{refCodon};

    return () unless defined $ref_codon;

    $ref_codon = '' if $ref_codon eq '-';
    $alt_codon = '' if $alt_codon eq '-';

    return ($ref_codon, $alt_codon);
}

sub _get_alleles {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;

    my $ref_tva = $bvfo->get_reference_VariationFeatureOverlapAllele;

    return () unless defined ($ref_tva);

    my $ref_allele = $ref_tva->variation_feature_seq;
    my $alt_allele = $bvfoa->variation_feature_seq;

    return () unless defined($ref_allele) and defined($alt_allele);

    $ref_allele = '' if $ref_allele eq '-';
    $alt_allele = '' if $alt_allele eq '-';

    return ($ref_allele, $alt_allele);
}

sub start_lost {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    my ($ref_pep, $alt_pep) = _get_peptide_alleles(@_);
    return 0 unless $bvfo->{startRef} ne $bvfo->{startAlt};
    # use cache for this method as it gets called a lot
    my $cache = $bvfoa->{_predicate_cache} ||= {};
    $cache->{start_lost} = 0;
    return $cache->{start_lost} = 1 if $bvfo->{startRef} ne $bvfo->{startAlt} && uc $bvfo->{startRef} eq "ATG";

    unless(exists($cache->{start_lost})) {

        # default
        $cache->{start_lost} = 0;

        return 0 unless _overlaps_start_codon(@_);

        $bvfo ||= $bvfoa->base_variation_feature_overlap;
        $feat ||= $bvfo->feature;
        $bvf  ||= $bvfo->base_variation_feature;

        # sequence variant
        if($bvfo->isa('consequence::TranscriptVariation')) {


            return $cache->{start_lost} = 1 if _ins_del_start_altered(@_) && !(inframe_insertion(@_) || inframe_deletion(@_));
            #check if _inv_start_altered makes a difference
            #return $cache->{start_lost} = 1 if _inv_start_altered(@_);

            my ($ref_pep, $alt_pep) = _get_peptide_alleles(@_);

            return 0 unless $ref_pep;

            # allow for introducing additional bases that retain start codon e.g. atg -> aCGAtg
            $cache->{start_lost} = (
                ($bvfo->translation_start == 1) and
                ($alt_pep !~ /\Q$ref_pep\E$/) and
                ($alt_pep !~ /^\Q$ref_pep\E/)
            );
        }


        # structural variant
        elsif($bvfo->isa('Bio::EnsEMBL::Variation::TranscriptStructuralVariation')) {
            my ($tr_crs, $tr_cre) = ($feat->coding_region_start, $feat->coding_region_end);
            return 0 unless defined($tr_crs) && defined($tr_cre);

            if($feat->strand == 1) {
                $cache->{start_lost} = overlap($tr_crs, $tr_crs + 2, $bvf->{start}, $bvf->{end});
            }
            else {
                $cache->{start_lost} = overlap($tr_cre-2, $tr_cre, $bvf->{start}, $bvf->{end});
            }
        }

        else {
            return 0;
        }
    }

    return $cache->{start_lost};
}

sub _inv_start_altered {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    # use cache for this method as it gets called a lot
    my $cache = $bvfoa->{_predicate_cache} ||= {};
    unless(exists($cache->{inv_start_altered})) {
        $cache->{inv_start_altered} = 0;

        return 0 if $bvfoa->isa('Bio::EnsEMBL::Variation::TranscriptStructuralVariationAllele');
        return 0 unless $bvfoa->seq_is_unambiguous_dna();
        return 0 unless _overlaps_start_codon(@_);

        $bvfo ||= $bvfoa->base_variation_feature_overlap;

        # get cDNA coords
        my ($cdna_start, $cdna_end) = ($bvfo->cdna_start, $bvfo->cdna_end);
        return 0 unless $cdna_start && $cdna_end;
        #print("$cdna_start\t$cdna_end\n");


        # make and edit UTR + translateable seq
        my $translateable = $bvfo->_translateable_seq();
        #print Dumper $translateable;

        my $utr = $bvfo->_five_prime_utr();
        #print("\n Are we Here \n");
	      return 0 unless $utr;
        my $utr_and_translateable = ($utr ? $utr->seq : '').$translateable;
        my $vf_feature_seq = $bvfoa->feature_seq;
        $vf_feature_seq = '' if $vf_feature_seq eq '-';
        my $atg_start = length($utr->seq);

        substr($utr_and_translateable, $cdna_start - 1, ($cdna_end - $cdna_start) + 1) = $vf_feature_seq;
        my $new_sc = substr($utr_and_translateable, $atg_start, 3);

        return $cache->{inv_start_altered} = 1 if substr($utr_and_translateable, $atg_start, 3) ne 'ATG';
    }

    return $cache->{inv_start_altered};
}

sub start_retained_variant {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;

    # return 0 if ($bvf->allele_string eq 'COSMIC_MUTATION' || $bvf->allele_string eq 'HGMD_MUTATION');

    my $pre = $bvfoa->_pre_consequence_predicates;

    return ($pre->{increase_length} || $pre->{decrease_length}) && _overlaps_start_codon(@_) && !_ins_del_start_altered(@_);
}

sub _overlaps_start_codon {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;

    my $cache = $bvfoa->{_predicate_cache} ||= {};

    unless(exists($cache->{overlaps_start_codon})) {
        $cache->{overlaps_start_codon} = 0;

        $bvfo ||= $bvfoa->base_variation_feature_overlap;
        $feat ||= $bvfo->feature;
        #return 0 if grep {$_->code eq 'cds_start_NF'} @{$feat->get_all_Attributes()};

        my ($cdna_start, $cdna_end) = ($bvfo->cdna_start, $bvfo->cdna_end);
        return 0 unless $cdna_start && $cdna_end;

        $cache->{overlaps_start_codon} = overlap(
            $cdna_start, $cdna_end,
            $feat->cdna_coding_start, $feat->cdna_coding_start + 2
        );
    }

    return $cache->{overlaps_start_codon};
}

sub _ins_del_start_altered {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;

    # use cache for this method as it gets called a lot
    my $cache = $bvfoa->{_predicate_cache} ||= {};

    unless(exists($cache->{ins_del_start_altered})) {
        $cache->{ins_del_start_altered} = 0;
        my ($ref_pep, $alt_pep) = _get_peptide_alleles(@_);

        return 0 if $bvfoa->isa('consequence::TranscriptStructuralVariationAllele');
        return 0 unless $bvfoa->seq_is_unambiguous_dna();
        return 0 unless _overlaps_start_codon(@_);

        my $pre = $bvfoa->_pre_consequence_predicates;
        return 0 unless $pre->{increase_length} || $pre->{decrease_length};

        $bvfo ||= $bvfoa->base_variation_feature_overlap;

        # get cDNA coords
        my ($cdna_start, $cdna_end) = ($feat->{'cdna_coding_start'}, $feat->{'cdna_coding_end'});
        return 0 unless $cdna_start && $cdna_end;

        # make and edit UTR + translateable seq
        my $translateable = $bvfo->_translateable_seq();
        if ($bvfo->{startRef} eq $bvfo->{startAlt}){
          return 1;
        }
        #my $utr = $bvfo->_five_prime_utr();
        #my $utr_and_translateable = ($utr ? $utr->seq : '').$translateable;

        #my $vf_feature_seq = $bvfoa->feature_seq;
        #$vf_feature_seq = '' if $vf_feature_seq eq '-';

        #substr($utr_and_translateable, $cdna_start - 1, ($cdna_end - $cdna_start) + 1) = $vf_feature_seq;

        # sequence shorter, we know it has been altered
        #return $cache->{ins_del_start_altered} = 1 if length($utr_and_translateable) < length($translateable);

        #$cache->{ins_del_start_altered} = $translateable ne substr($utr_and_translateable, 0 - length($translateable));
    }

    return $cache->{ins_del_start_altered};
}

sub synonymous_variant {
    my ($ref_pep, $alt_pep) = _get_peptide_alleles(@_);

    #print("\nsynonymous_variant\n");

    return 0 unless $ref_pep;

    return ( ($alt_pep eq $ref_pep) and (not stop_retained(@_) and ($alt_pep !~ /X/) and ($ref_pep !~ /X/)) );
}

sub missense_variant {
    my ($ref_pep, $alt_pep) = _get_peptide_alleles(@_);

    #print("\nmissense_variant\n");

    return 0 unless defined $ref_pep;

    return 0 if start_lost(@_);
    return 0 if stop_lost(@_);
    return 0 if stop_gained(@_);
    return 0 if partial_codon(@_);

    return ( $ref_pep ne $alt_pep ) && ( length($ref_pep) == length($alt_pep) );
}

sub inframe_insertion {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;
    $bvf  ||= $bvfo->base_variation_feature;

    # sequence variant
    if($bvf->isa('Bio::EnsEMBL::Variation::VariationFeature')) {
        my ($ref_codon, $alt_codon) = _get_codon_alleles(@_);

        return 0 if start_lost(@_);
        return 0 unless defined $ref_codon;
        return 0 unless ( length($alt_codon) > length ($ref_codon) );

        my ($ref_pep, $alt_pep) = _get_peptide_alleles(@_);

        return 0 unless defined($ref_pep) && defined($alt_pep);

        # not an inframe insertion if the inserted AA is before the start codon
        # we can use start_retained to check this
        return 0 if start_retained_variant(@_) && $alt_pep =~ /\Q$ref_pep\E$/;

        # if we have a stop codon in the alt peptide
        # trim off everything after it
        # this allows us to detect inframe insertions that retain a stop
        $alt_pep =~ s/\*.+/\*/;

        return 1 if ($alt_pep =~ /^\Q$ref_pep\E/) || ($alt_pep =~ /\Q$ref_pep\E$/);

    }

    # structural variant
    elsif($bvf->isa('Bio::EnsEMBL::Variation::StructuralVariationFeature')) {

        # TO BE DONE, NO WAY OF KNOWING WHAT SEQUENCE IS INSERTED YET
        return 0;

        # must be an insertion
        return 0 unless insertion(@_);

        my $cds_coords = $bvfo->cds_coords;

        if(scalar @$cds_coords == 1) {

            # wholly within exon
            if($cds_coords->[0]->isa('Bio::EnsEMBL::Mapper::Coordinate')) {
                1;
            }
        }

        # variant partially overlaps
        else {
            return 0;
        }
    }

    else {
        return 0;
    }
}

sub inframe_deletion {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;
    $bvf  ||= $bvfo->base_variation_feature;

    # sequence variant
    if($bvf->isa('consequence::VariationFeature')) {
        return 0 if partial_codon(@_);

        my ($ref_codon, $alt_codon) = _get_codon_alleles(@_);

        return 0 unless defined $ref_codon;
        return 0 unless length($alt_codon) < length ($ref_codon);
        return 0 unless ((length($ref_codon) - length($alt_codon)) % 3 == 0);

        # simple string match
        return 1 if ($ref_codon =~ /^\Q$alt_codon\E/) || ($ref_codon =~ /\Q$alt_codon\E$/);

        # check for internal match
        # relevant function code was copied from external file. line was:
        # ($ref_codon, $alt_codon) = @{Bio::EnsEMBL::Variation::Utils::Sequence::trim_sequences($ref_codon, $alt_codon)};
        # trim from left
        while($ref_codon && $alt_codon && substr($ref_codon, 0, 1) eq substr($alt_codon, 0, 1)) {
        $ref_codon = substr($ref_codon, 1);
        $alt_codon = substr($alt_codon, 1);
        }
        # trim from right
        while($ref_codon && $alt_codon && substr($ref_codon, -1, 1) eq substr($alt_codon, -1, 1)) {
        $ref_codon = substr($ref_codon, 0, length($ref_codon) - 1);
        $alt_codon = substr($alt_codon, 0, length($alt_codon) - 1);
        }

        # if nothing remains of $alt_codon,
        # then it fully matched a part in the middle of $ref_codon
        return length($alt_codon) == 0 && length($ref_codon) % 3 == 0;
    }

    # structural variant
    elsif($bvf->isa('Bio::EnsEMBL::Variation::StructuralVariationFeature')) {

        # must be a deletion
        return 0 unless deletion(@_);

        my $cds_coords = $bvfo->cds_coords;
        my $exons      = $bvfo->_exons;

        # in exon
        return (
           scalar @$cds_coords == 1 and
           $cds_coords->[0]->isa('Bio::EnsEMBL::Mapper::Coordinate') and
           scalar grep {complete_within_feature($bvfoa, $_, $bvfo, $bvf)} @$exons and
           $bvf->length() % 3 == 0
        );
    }

    else {
        return 0;
    }
}

sub stop_gained {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    #print("\nhere\n");
    #print Dumper $bvfoa;
    #print("\nstop_gained\n");

    # use cache for this method as it gets called a lot
    my $cache = $bvfoa->{_predicate_cache} ||= {};

    unless(exists($cache->{stop_gained})) {
        $cache->{stop_gained} = 0;

        ## check for inframe insertion before stop
        return 0 if stop_retained(@_);

        my ($ref_pep, $alt_pep) = _get_peptide_alleles(@_);

        return 0 unless defined $ref_pep;
        return 0 if(length $feat ->{stop_ref});
        $cache->{stop_gained} = ( ($alt_pep =~ /\*/) and ($ref_pep !~ /\*/) );
    }
    #print("\nend of function\n");
    #print Dumper $cache;
    return $cache->{stop_gained};
}

sub stop_lost {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    return 0 if stop_retained(@_);

    # use cache for this method as it gets called a lot
    my $cache = $bvfoa->{_predicate_cache} ||= {};

    unless(exists($cache->{stop_lost})) {
        $cache->{stop_lost} = 0;

        $bvfo ||= $bvfoa->base_variation_feature_overlap;
        $bvf  ||= $bvfo->base_variation_feature;
        $feat ||= $bvfo->feature;

        # sequence variant
        if($bvfoa->isa('consequence::TranscriptVariationAllele')) {

            # special case frameshift
    #        if(frameshift(@_)) {
    #          my $ref_pep = _get_ref_pep(@_);
    #          return $ref_pep && $ref_pep =~ /\*/;
    #        }

            my ($ref_pep, $alt_pep) = _get_peptide_alleles(@_);

            if(defined($ref_pep) && defined($alt_pep)) {
                $cache->{stop_lost} = ( ($alt_pep !~ /\*/) and ($ref_pep =~ /\*/) );
            }
            else {
                $cache->{stop_lost} = _ins_del_stop_altered(@_);
            }
        }

        # structural variant
        elsif($bvfoa->isa('Bio::EnsEMBL::Variation::TranscriptStructuralVariationAllele')) {
            return 0 unless deletion(@_);

            my ($tr_crs, $tr_cre) = ($feat->coding_region_start, $feat->coding_region_end);
            return 0 unless defined($tr_crs) && defined($tr_cre);

            if($feat->strand == 1) {
                $cache->{stop_lost} = overlap($tr_cre-2, $tr_cre, $bvf->{start}, $bvf->{end});
            }
            else {
                $cache->{stop_lost} = overlap($tr_crs, $tr_crs + 2, $bvf->{start}, $bvf->{end});
            }
        }

        else {
            return 0;
        }
    }

    return $cache->{stop_lost};
}

sub stop_retained {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;

    # use cache for this method as it gets called a lot
    my $cache = $bvfoa->{_predicate_cache} ||= {};

    unless(exists($cache->{stop_retained})) {

        # return 0 if ($bvf->allele_string eq 'COSMIC_MUTATION' || $bvf->allele_string eq 'HGMD_MUTATION');

        $cache->{stop_retained} = 0;

        $bvfo ||= $bvfoa->base_variation_feature_overlap;

        my $pre = $bvfoa->_pre_consequence_predicates;

        my ($ref_pep, $alt_pep) = _get_peptide_alleles(@_);
        my $altaa = $feat->{altaa};
        my $refaa = $feat->{refaa};

        if(defined($alt_pep) && $alt_pep ne '') {
            #return 0 if((length($feat->{stop_ref})) and $altaa =~/^\*/  );

                return 0 unless $ref_pep;

                $cache->{stop_retained} = ( $altaa =~ /^\*/ && $refaa =~ /^\*/ );
                if(length $feat->{stop_ref} && $feat->{stop_ref} =~ "TGA|TAA|TAG"){
                  my $alternate_aa = consequence::CodonTable->translate( $feat->{stop_alt}, 1,0);
                  $cache->{stop_retained} = ( $alternate_aa =~ /^\*/ && $feat->{stop_ref} =~ "TGA|TAA|TAG" )
                }

        }
        else {
            $cache->{stop_retained} = ($pre->{increase_length} || $pre->{decrease_length}) && _overlaps_stop_codon(@_) && !_ins_del_stop_altered(@_);
        }
    }

    return $cache->{stop_retained};
}

sub _overlaps_stop_codon {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;

    my $cache = $bvfoa->{_predicate_cache} ||= {};

    unless(exists($cache->{overlaps_stop_codon})) {
        $cache->{overlaps_stop_codon} = 0;

        $bvfo ||= $bvfoa->base_variation_feature_overlap;
        $feat ||= $bvfo->feature;
        #return 0 if grep {$_->code eq 'cds_end_NF'} @{$feat->get_all_Attributes()};

        my ($cdna_start, $cdna_end) = ($bvfo->cdna_start, $bvfo->cdna_end);
        return 0 unless $cdna_start && $cdna_end;

        $cache->{overlaps_stop_codon} = overlap(
            $cdna_start, $cdna_end,
            $feat->cdna_coding_end - 2, $feat->cdna_coding_end
        );
    }

    return $cache->{overlaps_stop_codon};
}

sub _ins_del_stop_altered {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;

    # use cache for this method as it gets called a lot
    my $cache = $bvfoa->{_predicate_cache} ||= {};

    unless(exists($cache->{ins_del_stop_altered})) {
        $cache->{ins_del_stop_altered} = 0;

        return 0 if $bvfoa->isa('Bio::EnsEMBL::Variation::TranscriptStructuralVariationAllele');
        return 0 unless $bvfoa->seq_is_unambiguous_dna();
        return 0 unless _overlaps_stop_codon(@_);

        my $pre = $bvfoa->_pre_consequence_predicates;
        return 0 unless $pre->{increase_length} || $pre->{decrease_length};

        $bvfo ||= $bvfoa->base_variation_feature_overlap;

        # get cDNA coords and CDS start
        my ($cdna_start, $cdna_end, $cds_start) = ($bvfo->cdna_start, $bvfo->cdna_end, $bvfo->cds_start);
        return 0 unless $cdna_start && $cdna_end && $cds_start;

        # make and edit UTR + translateable seq
        my $translateable = $bvfo->_translateable_seq();
        my $utr = $bvfo->_three_prime_utr();

        my $utr_and_translateable = $translateable.($utr ? $utr->seq : '');

        my $vf_feature_seq = $bvfoa->feature_seq;
        $vf_feature_seq = '' if $vf_feature_seq eq '-';

        # use CDS start to anchor the edit
        # and cDNA coords to get the length (could use VF, but have already retrieved cDNA coords)
        substr($utr_and_translateable, $cds_start - 1, ($cdna_end - $cdna_start) + 1) = $vf_feature_seq;

        # new sequence shorter, we know it has been altered
        return $cache->{ins_del_stop_altered} = 1 if length($utr_and_translateable) < length($translateable);

        # now we need the codon from the new seq at the equivalent end pos from translateable
        # and to translate it to check if it is still a stop
        my $pep = Bio::Seq->new(
            -seq        => substr($utr_and_translateable, length($translateable) - 3, 3),
            -moltype    => 'dna',
            -alphabet   => 'dna',
        )->translate(
            undef, undef, undef, $bvfo->_codon_table
        )->seq;

        $cache->{ins_del_stop_altered} = !($pep && $pep eq '*');
    }

    return $cache->{ins_del_stop_altered};
}

sub frameshift {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    $bvfo ||= $bvfoa->base_variation_feature_overlap;

    # sequence variant
    if($bvfoa->isa('consequence::TranscriptVariationAllele')) {

        return 0 if partial_codon(@_);

        # Trigger calculation of codons if they're not available
        _get_peptide_alleles(@_) unless defined $feat->{refCodon} && defined $feat->{altCodon};
        my $refLen = length($feat->{refCodon});
        my $altLen = length($feat->{altCodon});
        return abs($refLen - $altLen) % 3;
    }

    # structural variant
    #elsif($bvfoa->isa('Bio::EnsEMBL::Variation::TranscriptStructuralVariationAllele')) {
    #    my $exons = $bvfo->_exons;

    #    return (
    #        (
    #            deletion(@_) or
    #            copy_number_loss(@_)
    #        ) and
    #        scalar grep {complete_within_feature($bvfoa, $_, $bvfo, $bvf)} @$exons and
    #        $bvf->length % 3 != 0
    #    );

        # TODO INSERTIONS
    #}

    else {
        return 0;
    }
}

sub partial_codon {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;

    # use cache for this method as it gets called a lot
    my $cache = $bvfoa->{_predicate_cache} ||= {};

    unless(exists($cache->{_partial_codon})) {

        # default
        $cache->{_partial_codon} = 0;

        $bvfo ||= $bvfoa->base_variation_feature_overlap;

        return 0 unless defined $bvfo->translation_start;

        my $cds_length = length $bvfo->_translateable_seq;

        my $codon_cds_start = ($bvfo->translation_start * 3) - 2;

        my $last_codon_length = $cds_length - ($codon_cds_start - 1);

        $cache->{_partial_codon} = ( $last_codon_length < 3 and $last_codon_length > 0 );
    }

    return $cache->{_partial_codon};
}

sub coding_unknown {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;

    # sequence variant
    if($bvfoa->isa('consequence::TranscriptVariationAllele')) {
        return (
            within_cds(@_) and (
                (not $bvfoa->peptide) or
                (not _get_peptide_alleles(@_)) or
                ($bvfoa->peptide =~ /X/) or
                ((_get_peptide_alleles(@_))[0] =~ /X/)
            ) and (
                not (
                    frameshift(@_) or inframe_deletion(@_) or protein_altering_variant(@_) or
                    start_retained_variant(@_) or start_lost(@_) or
                    stop_retained(@_) or stop_lost(@_)
                )
            )
        );
    }

    # structural variant
    elsif($bvfoa->isa('Bio::EnsEMBL::Variation::TranscriptStructuralVariationAllele')) {
        return (within_cds(@_) and not(inframe_insertion(@_) or inframe_deletion(@_) or frameshift(@_)));
    }

    else {
        return 0;
    }
}

#package Bio::EnsEMBL::Variation::RegulatoryFeatureVariationAllele;

sub within_regulatory_feature {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    return within_feature(@_);
}

#package Bio::EnsEMBL::Variation::ExternalFeatureVariationAllele;

sub within_external_feature {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    return (within_feature(@_) and (not within_miRNA_target_site(@_)));
}

#sub within_miRNA_target_site {
#    my $efva = shift;
#
#    my $fset = $efva->variation_feature_overlap->feature->feature_set;
#
#    return ($fset && $fset->name eq 'miRanda miRNA targets');
#}

#package Bio::EnsEMBL::Variation::MotifFeatureVariationAllele;

#sub within_motif_feature {
#    my $mfva = shift;
#    return (
#        within_feature($mfva) and
#        !increased_binding_affinity($mfva) and
#        !decreased_binding_affinity($mfva)
#    );
#}

sub within_motif_feature {
    my ($bvfoa, $feat, $bvfo, $bvf) = @_;
    return within_feature(@_);
}

#sub increased_binding_affinity {
#    my $mfva = shift;
#    my $change = $mfva->binding_affinity_change;
#    return (within_feature($mfva) and (defined $change) and ($change > 0));
#}
#
#sub decreased_binding_affinity {
#    my $mfva = shift;
#    my $change = $mfva->binding_affinity_change;
#    return (within_feature($mfva) and (defined $change) and ($change < 0));
#}

sub contains_entire_feature {
    my $vfo = shift;

    my $bvf  = $vfo->base_variation_feature;
    my $feat = $vfo->feature;

    return ( ($bvf->{start} <= $feat->{start}) && ($bvf->{end} >= $feat->{end}) );
}

1;
