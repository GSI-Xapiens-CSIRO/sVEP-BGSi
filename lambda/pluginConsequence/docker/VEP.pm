#!/usr/bin/perl
=head1 LICENSE

Copyright [1999-2015] Wellcome Trust Sanger Institute and the EMBL-European Bioinformatics Institute
Copyright [2016-2019] EMBL-European Bioinformatics Institute

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
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

# EnsEMBL module for Bio::EnsEMBL::Variation::Utils::Sequence
#
#

=head1 NAME

Bio::EnsEMBL::Variation::Utils::VEP - Methods used by the Variant Effect Predictor

=head1 SYNOPSIS

  use Bio::EnsEMBL::Variation::Utils::VEP qw(configure);

  my $config = configure();

=head1 METHODS

=cut

package VEP;

use strict;
use warnings;

#package lib::consequence::VEP;

# module list
use Getopt::Long;
use FileHandle;
use File::Path qw(mkpath);
use Storable qw(nstore_fd fd_retrieve freeze thaw);
use Scalar::Util qw(weaken looks_like_number);
use Digest::MD5 qw(md5_hex);
use IO::Socket;
use IO::Select;
use Exporter;
use Data::Dumper;
use JSON;
use File::Basename qw(dirname);
use Cwd  qw(abs_path);
use lib dirname(dirname abs_path $0) . 'var/task/';
use consequence::VariationFeature;
use consequence::Transcript;
use consequence::TranscriptVariation;
use consequence::TranscriptVariationAllele;
use Try::Tiny;
use File::Temp qw(tempfile);
use Encode qw(encode);

my $config = {};
my $fastaLocation = "s3://$ENV{'REFERENCE_LOCATION'}/";
my $spliceFile =  $ENV{'SPLICE_REFERENCE'};
my $nextFunctionSnsTopicArn =  $ENV{'NEXT_FUNCTION_SNS_TOPIC_ARN'};
my $mirnaFile =  $ENV{'MIRNA_REFERENCE'};
my $fastaBase =  $ENV{'FASTA_REFERENCE_BASE'};
my $outputLocation =  $ENV{'SVEP_REGIONS'};
my $tempLocation =  $ENV{'SVEP_TEMP'};
my $filterConsequenceRank = $ENV{'FILTER_CONSEQUENCE_RANK'};
my $dynamoClinicJobsTable = $ENV{'DYNAMO_CLINIC_JOBS_TABLE'};
my $functionName = $ENV{'AWS_LAMBDA_FUNCTION_NAME'};
my $sendJobEmailArn = $ENV{'SEND_JOB_EMAIL_ARN'};
my $maxSnsMessageSize = 260000;
my $s3PayloadKey = "_s3_payload_key";
my $processedRecords = 0;

sub handle {
    my ($payload) = @_;
    simple_truncated_print("Received message: $payload\n");
    my $event = decode_json($payload);
    my $sns = $event->{Records}[0]{Sns};
    ##########################################update
    my $message = decode_json($sns->{'Message'}); #might have to remove decode_json
    my $payloadKey = $message->{$s3PayloadKey};
    if (defined $payloadKey) {
      print("Loading payload from S3 bucket $tempLocation and key: $payloadKey\n");
      my $payloadFile = "/tmp/payload.json";
      system("/usr/bin/aws s3 cp s3://$tempLocation/$payloadKey $payloadFile 1>/dev/null");
      my $messageString;
      {
        local $/;
        open(my $fh, '<', $payloadFile) or die "can't open $payloadFile: $!";
        $messageString = <$fh>;
      }
      simple_truncated_print("Payload from S3: $messageString\n");
      $message = decode_json($messageString);
    }
    my @data = $message->{'snsData'};
    my $request_id = $message->{'requestId'};
    my $tempFileName = $message->{'tempFileName'};
    my $refChrom = $message->{'refChrom'};
    print("tempFileName is - $tempFileName\n");
    #############################################

    try {
      my $fasta = $fastaBase.'.'.$refChrom.'.fa.bgz';
      print "Copying fasta reference files.\n";
      system("/usr/bin/aws s3 cp $fastaLocation /tmp/ --recursive  --exclude '*'  --include '$fasta*' 1>/dev/null");
      print "Copying splice reference files.\n";
      system("/usr/bin/aws s3 cp $fastaLocation /tmp/ --recursive  --exclude '*'  --include '$spliceFile*' 1>/dev/null");
      my @results;
      while(@data){
        my $region = shift @data;
        foreach my $line (@{$region}){
          if ( scalar(@{$line->{'data'}}) == 1 && @{$line->{'data'}}[0] eq ''){
            next;
          }
          my @vep = parse_vcf($line, $refChrom);
          if(scalar(@vep)) {
            push @results, @vep;
          }
        }
      }
      print("Passed ", scalar(@results), "/$processedRecords records with rank >= $filterConsequenceRank\n");
      if (scalar(@results) > 0) {
        my %outMessage = (
          'snsData' => \@results,
          'refChrom' => $refChrom,
          'requestId' => $request_id,
        );
        start_function($nextFunctionSnsTopicArn, $tempFileName, \%outMessage);
      }

      my $tempOut = 's3://'.$tempLocation.'/'.$tempFileName;
      system("/usr/bin/aws s3 rm $tempOut");
      print("Cleaning /tmp/\n");
      system("rm -rf /tmp/*");
      print("Task Complete.\n");
    }
    catch {
     handle_failed_execution($request_id, $functionName, $_);
    };
}

sub handle_failed_execution {
    my ($request_id, $failed_step, $error_message) = @_;

    my $query_result = `/usr/bin/aws dynamodb get-item --table-name $dynamoClinicJobsTable --key '{"job_id":{"S":"$request_id"}}' --output json 2>&1`;
    die "Failed to query DynamoDB: $query_result" if $? != 0;
    my $query_json;
    eval { $query_json = decode_json($query_result); };
    if ($@) {
      warn "Error parsing JSON response: $@";
      $query_json = {};
    }

    # Check if item exists and job_status is already "failed"
    if (exists $query_json->{Item} && 
        exists $query_json->{Item}->{job_status} && 
        $query_json->{Item}->{job_status}->{S} eq "failed") {
        return;
    }


    # Prepare the update expression
    my $update_expression = "SET #job_status = :job_status, #failed_step = :failed_step, #error_message = :error_message";
    my $expression_attribute_names = encode_json({
        "#job_status"        => "job_status",
        "#failed_step"   => "failed_step",
        "#error_message" => "error_message"
    });
    my $expression_attribute_values = encode_json({
        ":job_status"        => { "S" => "failed" },
        ":failed_step"   => { "S" => $failed_step },
        ":error_message" => { "S" => $error_message }
    });

    # Update the item in DynamoDB
    my $system_call = "/usr/bin/aws dynamodb update-item --table-name $dynamoClinicJobsTable " .
      "--key '{\"job_id\":{\"S\":\"$request_id\"}}' " .
      "--update-expression \"$update_expression\" " .
      "--expression-attribute-names '$expression_attribute_names' " .
      "--expression-attribute-values '$expression_attribute_values'";
    print("System call: $system_call\n");
    my $exit_code = system($system_call);

    die "DynamoDB update failed with exit code " . ($exit_code >> 8) if $exit_code != 0;
    
    # Send SNS Email Job notification
    sns_publish($sendJobEmailArn, {
        job_id           => $request_id,
        job_status       => "failed",
        project_name     => $query_json->{Item}->{project_name}->{S},
        input_vcf        => $query_json->{Item}->{input_vcf}->{S},
        user_id          => $query_json->{Item}->{uid}->{S},
        is_from_failed_execution => JSON::true
    });   

    die "$error_message\n";
}

sub create_temp_file {
  my ($nextTempFile) = @_;
  print("Creating file: $nextTempFile\n");
  system("aws", "s3api", "put-object", "--bucket", $tempLocation, "--key",  $nextTempFile, "--content-length", "0");
}

sub sns_publish {
  my ($topicArn, $message, $s3PayloadPrefix) = @_;
  my $jsonMessage = to_json($message);
  # In order to get around command-line character limits, we must pass the message as a file
  # https://github.com/aws/aws-cli/issues/1314#issuecomment-515674161
  my $filename = "/tmp/message.json";
  print("Saving message to local file $filename\n");
  open(my $fh, '>', $filename) or die "Could not open file '$filename' $!";
  print $fh $jsonMessage;
  close $fh;
  my $messageString = "file://$filename";
  my $messageSize = length($jsonMessage);
  if ($messageSize > $maxSnsMessageSize && defined $s3PayloadPrefix) {
    print("SNS message too large ($messageSize bytes), uploading to S3\n");
    my $payloadKey = "payloads/$s3PayloadPrefix.json";
    simple_truncated_print("Uploading to S3 bucket $tempLocation and key $payloadKey: $jsonMessage\n");
    system("/usr/bin/aws s3 cp $filename s3://$tempLocation/$payloadKey 1>/dev/null");
    my %s3Map = ($s3PayloadKey => $payloadKey);
    $jsonMessage = to_json(\%s3Map);
    $messageString = $jsonMessage;
  }
  simple_truncated_print("Calling SNS Publish with topicArn: $topicArn and message: $jsonMessage\n");
  system("aws", "sns", "publish", "--topic-arn", $topicArn, "--message", $messageString);
}

sub start_function {
  my ($topicArn, $baseFilename, $message) = @_;
  my $functionName = (split(":", $topicArn))[-1];
  my $fileName = $baseFilename."_".$functionName;
  $message->{'tempFileName'} = $fileName;
  create_temp_file($fileName);
  sns_publish($topicArn, $message, $fileName);
}

sub simple_truncated_print {
  # This doesn't need to be precise, just good enough
  my $maxLength = 1000;
  my ($string) = @_;
  my $toRemove = length($string) - $maxLength;
  if($toRemove > 0){
    $string = substr($string, 0, $maxLength / 2)."<$toRemove bytes>".substr($string, -$maxLength / 2);
  }
  print($string);
}

# parse a line of VCF input into a variation feature object
sub parse_vcf {
    my ($line, $refChrom) = @_;
    #print Dumper $line;
    my ($chr, $start, $end, $ref, $alt) = ($line->{'chrom'}, $line->{'posVcf'}, $line->{'posVcf'}, $line->{'refVcf'}, $line->{'altVcf'});
    #print("$chr\t$start\n");
    my @data = @{$line->{'data'}};
    if($data[0] eq ""){
      return;
    }
    my (@transcripts,@transcriptIds,@features) = ();

    # non-variant
    my $non_variant = 0;

    if($alt eq '.') {
        $non_variant = 1;
    }
    # adjust end coord
    $end += (length($ref) - 1);

    # find out if any of the alt alleles make this an insertion or a deletion
    my ($is_indel, $is_sub, $ins_count, $total_count);
    foreach my $alt_allele(split ',', $alt) {
        $is_indel = 1 if $alt_allele =~ /^[DI]/;
        $is_indel = 1 if length($alt_allele) != length($ref);
        $is_sub = 1 if length($alt_allele) == length($ref);
        $ins_count++ if length($alt_allele) > length($ref);
        $total_count++;
    }
    # multiple alt alleles?
    if($alt =~ /\,/) {
        if($is_indel) {
            my @alts;

            # find out if all the alts start with the same base
            # ignore "*"-types
            my %first_bases = map {substr($_, 0, 1) => 1} grep {!/\*/} ($ref, split(',', $alt));

            if(scalar keys %first_bases == 1) {
                $ref = substr($ref, 1) || '-';
                $start++;

                foreach my $alt_allele(split ',', $alt) {
                    $alt_allele = substr($alt_allele, 1) unless $alt_allele =~ /\*/;
                    $alt_allele = '-' if $alt_allele eq '';
                    push @alts, $alt_allele;
                }
            }
            else {
                push @alts, split(',', $alt);
            }

            $alt = join "/", @alts;
        }

        else {
            # for substitutions we just need to replace ',' with '/' in $alt
            $alt =~ s/\,/\//g;
        }
    }

    elsif($is_indel) {

        # insertion or deletion (VCF 4+)
        if(substr($ref, 0, 1) eq substr($alt, 0, 1)) {

            # chop off first base
            $ref = substr($ref, 1) || '-';
            $alt = substr($alt, 1) || '-';

            $start++;
        }
    }


    ######Start of my code for processing GTF #############
    while(@data){
      my $element = shift @data;
      if ($element =~ /transcript_id\s\"(\w+)\"\;/){
        push @transcriptIds, $1;
      }
      my @type =(split /\t/, $element);
      if ($type[2] eq "transcript"){
        push @transcripts,$element;
      }else{
        push @features,$element;
      }
    }
    my @uniqueTranscriptIds = do { my %seen; grep { !$seen{$_}++ } @transcriptIds };
    my @results;
    my %transcriptHash;
    $transcriptHash{$_}++ for (@uniqueTranscriptIds);

    my $intron_result;
    foreach my $transcript (@transcripts){
      my @rows = (split /\t/, $transcript,-1);
      #print Dumper @rows;
      my %info = ();
      my ($seq,$length,$tr,$strand,$vf);

      foreach my $bit(split ';', ($rows[8])) {
          my ($key, $value) = split ' ', $bit, -1;    ##GTF info field passed by lambda contains key value separated by space.
          #print("$key\t$value\n");
          $value =~ s/"//g;
          $info{$key} = $value;
      }
      #print Dumper %info;
      foreach my $feature(@features){
        my @featurerows = (split /\t/, $feature, -1);
        my @info = (split ';', $featurerows[8],-1);
        my ($key, $value) = split ' ', $info[2],-1;
        $value =~ s/"//g;
        if($value eq $info{'transcript_id'}){
          if($featurerows[2] eq "exon"){
            $info{'exon'} = 1;
            $info{'exon_start'} = $featurerows[3];
            $info{'exon_end'} = $featurerows[4];
            my ($key1, $value1) = split ' ', $info[4],-1;
            $value1 =~ s/"//g;
            $info{'exon_number'} = $value1;
          }
          if($featurerows[2] eq "CDS" ){
            $info{'CDS'} = 1;
            $info{'CDS_start'} = $featurerows[3];
            $info{'CDS_end'} = $featurerows[4];
            $info{'CDS_frame'} = $featurerows[7];
          }
          if( $featurerows[2] eq "start_codon" || $featurerows[2] eq "stop_codon"){ #COULD ALSO BE start or stop codon
            $info{'CDS'} = 1;
            $info{'start_stop'} = 1;
            $info{'CDS_start'} = $featurerows[3];
            $info{'CDS_end'} = $featurerows[4];
            $info{'CDS_frame'} = $featurerows[7];
          }
          if($featurerows[2] eq "three_prime_utr"){
            $info{'three_prime_utr'} = 1;
            $info{'three_prime_utr_start'} = $featurerows[3];
            $info{'three_prime_utr_end'} = $featurerows[4];
          }
          if($featurerows[2] eq "five_prime_utr"){
            $info{'five_prime_utr'} = 1;
            $info{'five_prime_utr_start'} = $featurerows[3];
            $info{'five_prime_utr_end'} = $featurerows[4];
          }
        }
      }

      #print Dumper %info;
      #exit()

      my $original_alt = $alt;

      if($rows[6] =~ /^[+]/){
        $strand=1;
      }
      else{
        $strand = -1;
      }

      if( !$intron_result ){
        my $file = "/tmp/".$spliceFile;
        my $intronStart = $start - 8;
        my $intronEnd = $start + 8;
        my $location = $refChrom.":".$intronStart."-".$intronEnd;
        $intron_result =  `./tabix $file $location`;
        #print("\n Intron result = $intron_result")
      }

      if(exists($info{'exon'})){

        # create VF object
        $vf = consequence::VariationFeature->new_fast({
            start          => $start,
            end            => $end,
            allele_string  => $non_variant ? $ref : $ref.'/'.$alt,
            strand         => $strand,
            map_weight     => 1,
            #adaptor        => $config->{vfa}, Need to get rid of this from variationFeature as Well
            variation_name => undef ,
            chr            => $chr,
            seq_region_start => $info{'exon_start'},
            seq_region_end => $info{'exon_end'},
            exon         => 1,
        });
        my $intron_boundary = 0;
        my $splice_region_variant =0;
        if(exists($info{'CDS'})){
          my $location = $refChrom.':'.$info{'CDS_start'}.'-'.$info{'CDS_end'};
          my $fasta ='Homo_sapiens.GRCh38.dna.chromosome.'.$refChrom.'.fa.bgz';
          my $file = '/tmp/'.$fasta;
          $vf->{'fasta_file'} = $file;
          $vf->{'gtf_file'} = "/tmp/".$spliceFile;
          $vf->{'reference_chr'} = $refChrom;
          my @result = `./samtools faidx $file $location`;
          shift @result;
          $seq = join "", @result;
          $seq =~ s/[\r\n]+//g;
          $length = abs($info{'CDS_end'}-$info{'CDS_start'}) + 1;

          for my $tran (split /[\r\n]+/, $intron_result){
            my @infoNew = (split '\t', $tran);
            if($infoNew[2] eq "exon" && $infoNew[7] ne $info{transcript_id}  ){
              if( (($info{'CDS_end'} - $start) =~ /^[0-3]$/) || (($start - $info{'CDS_start'} ) =~ /^[0-3]$/) ){
                $intron_boundary =1;
                $splice_region_variant =1;
              }
            }
          }
          if(exists($info{'start_stop'} )){
            $intron_boundary =0;
          }

          $tr = consequence::Transcript->new_fast({
              stable_id          => $info{transcript_id},
              version            => $info{transcript_version},
              external_name  => $info{transcript_name},
              source         => $info{transcript_source},
              biotype     => $info{transcript_biotype},
              confidence => $info{transcript_support_level},
              start => $rows[3],
              end => $rows[4],
              cds => 1,
              intron_boundary => $intron_boundary,
              splice_region_variant => $splice_region_variant,
              cdna_coding_start => $info{'CDS_start'},
              cdna_coding_end => $info{'CDS_end'},
              cds_frame => $info{'CDS_frame'},
              strand => $strand,
              seq => $seq,
              seq_length => $length,
              position => $start,
              ref_allele => $ref,
              alt_allele => $alt,
          });
        }elsif(exists($info{'three_prime_utr'}) ){
          for my $tran (split /[\r\n]+/, $intron_result){
            my @infoNew = (split '\t', $tran);
            if($infoNew[2] eq "exon" && $infoNew[7] ne $info{transcript_id}){
              if(  ((($info{'exon_end'} - $start) =~ /^[0-3]$/ )|| (($start - $info{'exon_start'}) =~ /^[0-3]$/ ) )) {
                $intron_boundary =1;
                $splice_region_variant=1;
              }
            }
          }

          $tr = consequence::Transcript->new_fast({
              stable_id          => $info{transcript_id},
              version            => $info{transcript_version},
              external_name  => $info{transcript_name},
              source         => $info{transcript_source},
              biotype     => $info{transcript_biotype},
              confidence => $info{transcript_support_level},
              start => $rows[3],
              end => $rows[4],
              three_prime_utr => 1,
              exon_start => $info{'exon_start'},
              exon_end => $info{'exon_end'},
              strand => $strand,
              intron_boundary => $intron_boundary,
              splice_region_variant => $splice_region_variant,
              #seq => $seq,
              #seq_length => $length,
              position => $start,
              ref_allele => $ref,
              alt_allele => $alt,
          });
        }elsif(exists($info{'five_prime_utr'})){
          for my $tran (split /[\r\n]+/, $intron_result){
            my @infoNew = (split '\t', $tran);
            if($infoNew[2] eq "exon" && $infoNew[7] ne $info{transcript_id}){
              if( (($info{'exon_end'} - $start) =~ /^[0-3]$/) || (($start - $info{'exon_start'}) =~ /^[0-3]$/)  ){
                $intron_boundary =1;
                $splice_region_variant = 1;
                #print("\nsplice\n");
              }
            }
          }

          $tr = consequence::Transcript->new_fast({
              stable_id          => $info{transcript_id},
              version            => $info{transcript_version},
              external_name  => $info{transcript_name},
              source         => $info{transcript_source},
              biotype     => $info{transcript_biotype},
              confidence => $info{transcript_support_level},
              start => $rows[3],
              end => $rows[4],
              five_prime_utr => 1,
              exon_start => $info{'exon_start'},
              exon_end => $info{'exon_end'},
              strand => $strand,
              splice_region_variant => $splice_region_variant,
              intron_boundary => $intron_boundary,
              #seq => $seq,
              #seq_length => $length,
              position => $start,
              ref_allele => $ref,
              alt_allele => $alt,
          });
        }else{
          for my $tran (split /[\r\n]+/, $intron_result){
            my @infoNew = (split '\t', $tran);
            if($infoNew[2] eq "exon" && $infoNew[7] ne $info{transcript_id}){
              if( (($info{'exon_end'} - $start) =~ /^[0-3]$/) || (($start - $info{'exon_start'}  ) =~ /^[0-3]$/) ){
                $intron_boundary =1;
                $splice_region_variant = 1;
                #print("\nsplice\n");
              }
            }
          }
          $tr = consequence::Transcript->new_fast({
              stable_id          => $info{transcript_id},
              version            => $info{transcript_version},
              external_name  => $info{transcript_name},
              source         => $info{transcript_source},
              biotype     => $info{transcript_biotype},
              confidence => $info{transcript_support_level},
              start => $rows[3],
              end => $rows[4],
              strand => $strand,
              exon_start => $info{'exon_start'},
              exon_end => $info{'exon_end'},
              intron_boundary => $intron_boundary,
              splice_region_variant => $splice_region_variant,
              #seq => $seq,
              #seq_length => $length,
              position => $start,
              ref_allele => $ref,
              alt_allele => $alt,
          });
        }

        my $mirnaLocalFile = "/tmp/".$mirnaFile;
        unless (-e $mirnaLocalFile) {
          print "Copying: $mirnaFile\n";
          system("/usr/bin/aws s3 cp $fastaLocation /tmp/ --recursive  --exclude '*'  --include '$mirnaFile*' 1>/dev/null");
        }
        if($rows[1] eq "mirbase"){
          #my $intron_loc = $start;
          my $location = "chr".$refChrom.":".$start."-".$start;
          my $mirna_result =  `./tabix $mirnaLocalFile $location`;
          if(length $mirna_result){
            $tr->{within_mirna} = 1;
          }else{
            $tr->{within_mirna} = 0;
          }

        }

      }else{
        # create VF object
        $vf = consequence::VariationFeature->new_fast({
            start          => $start,
            end            => $end,
            allele_string  => $non_variant ? $ref : $ref.'/'.$alt,
            strand         => $strand,
            map_weight     => 1,
            variation_name => undef ,
            chr            => $chr,
            intron         => 1,
        });
        $tr = consequence::Transcript->new_fast({
            stable_id          => $info{transcript_id},
            version            => $info{transcript_version},
            external_name  => $info{transcript_name},
            source         => $info{transcript_source},
            biotype     => $info{transcript_biotype},
            confidence => $info{transcript_support_level},
            start => $rows[3],
            end => $rows[4],
            strand => $strand,
            position => $start,
            ref_allele => $ref,
            alt_allele => $alt,
            #intron_boundary => 1,
        });

        for my $tran (split /[\r\n]+/, $intron_result){
          my @info = (split '\t', $tran);
          if( ($info[6] eq '+') && $info{transcript_id} eq $info[7] && (($info[3] > $end) && ( $info[3] - $end) < 3+($end-$start)) ){
              $tr->{'splice_acceptor_variant'} =1;
              $tr->{'intron_boundary'} =1;
              $vf->{'intron'} = 0;
              last;
          }elsif( ($info[6] eq '+') && $info{transcript_id} eq $info[7] && (($end > $info[4]) && ( $end - $info[4]) < 3+($end-$start))){
              $tr->{'splice_donor_variant'} =1;
              $tr->{'intron_boundary'} =1;
              $vf->{'intron'} = 0;
              last;
          }elsif( ($info[6] eq '-') && $info{transcript_id} eq $info[7] && (($info[3] > $end) &&( $info[3] - $end) < 3+($end-$start)) ){
              $tr->{'splice_donor_variant'} =1;
              $tr->{'intron_boundary'} =1;
              $vf->{'intron'} = 0;
              last;
          }elsif(($info[6] eq '-') && $info{transcript_id} eq $info[7] && (($end > $info[4]) && ( $end - $info[4]) < 3+($end-$start))){
              $tr->{'splice_acceptor_variant'} =1;
              $tr->{'intron_boundary'} =1;
              $vf->{'intron'} = 0;
              last;
          }elsif( (( ($info[3] - $end) > 0) &&(($info[3] - $end) < 9) && $info{transcript_id} eq $info[7])||
          (( ($end - $info[4]) > 0)&&(($end - $info[4]) < 9) && $info{transcript_id} eq $info[7]) ) {
            $tr->{'splice_region_variant'} =1;
            $tr->{'intron_boundary'} =1;
            #last;
          }
        }

      }

      # flag as non-variant
      $vf->{non_variant} = 1 if $non_variant;
      #print Dumper $tr;


      my $tv = $vf->add_TranscriptVariation(
              consequence::TranscriptVariation->new(
                  -variation_feature  => $vf,
                  -transcript         => $tr,
              )
      );

      my ($cons, $rank) = vf_to_consequences($vf);

      if(exists($tr->{'three_prime_utr'})){
        if( $cons eq 'intergenic_variant'){
          $cons = '3_prime_UTR_variant'
        }else{
        $cons = '3_prime_UTR_variant,'.$cons;
        }
      }
      if(exists($tr->{'five_prime_utr'})){
        if( $cons eq 'intergenic_variant'){
          $cons = '5_prime_UTR_variant'
        }else{
        $cons = '5_prime_UTR_variant,'.$cons;
        }
      }
      my $start_end_string = $start<$end ? $start.'-'.$end : $end.'-'.$start;
      my %record = (
        %{$line},
        rank => $rank,
        region => $chr.':'.$start_end_string,
        alt => $alt,
        consequence => $cons,
        geneName => (defined $info{gene_name} ? $info{gene_name} : '-'),
        geneId => $info{gene_id},
        feature => $rows[2],
        transcriptId => $info{transcript_id}.".".$info{transcript_version},
        transcriptBiotype => $info{transcript_biotype},
        exonNumber => ($info{exon_number} || '-'),
        aminoAcids => ($tv->{feature}{aa} || '-'),
        codons => ($tv->{feature}{codons} || '-'),
        strand => $strand,
        transcriptSupportLevel => ($info{transcript_support_level}|| '-'),
        ref => $ref,
      );
      delete $record{"data"};  # This particular value is very large and no longer needed
      if(length $tr->{warning}){
        $record{warning} = $tr->{warning};
      }
      # Filter out records of low rank
      $processedRecords++;
      if($record{rank} <= $filterConsequenceRank){
        push @results, \%record;
      }
    }
    my @sorted = sort { $a->{rank} <=> $b->{rank} } @results;
    return @sorted;

    #print Dumper @sorted;

    #my $PutObjectOutput = $s3->PutObject(
    #  Bucket             => $outputLocation,
    #  Key                => $filename,                 # OPTIONAL
    #  Body               => join("\n", @sorted),
    #  );
    #print($PutObjectOutput->ETag);

}

# takes a variation feature and returns ready to print consequence information
sub vf_to_consequences {
  my $vf = shift;
  my $vf_ref = ref($vf);

  my @return = ();

  my $allele_method = defined($config->{process_ref_homs}) ? 'get_all_' : 'get_all_alternate_';

  # get all VFOAs
  # need to be sensitive to whether --regulatory or --coding_only is switched on
  my $vfos;
  my $method = $allele_method.'VariationFeatureOverlapAlleles';

  # include regulatory stuff?
  if(!defined $config->{coding_only} && defined $config->{regulatory}) {
    $vfos = $vf->get_all_VariationFeatureOverlaps;
  }
  # otherwise just get transcript & intergenic ones
  else {
    @$vfos = grep {defined($_)} (
      @{$vf->get_all_TranscriptVariations}
#      $vf->get_IntergenicVariation
    );
  }

  # grep out non-coding?
  @$vfos = grep {$_->can('affects_cds') && $_->affects_cds} @$vfos if defined($config->{coding_only});
  #print Dumper $vfos;
  # get alleles
  my @vfoas = map {@{$_->$method}} @{$vfos};

    my $line;
    my $term_method = 'SO_term';

    my @ocs = sort {$a->rank <=> $b->rank} map {@{$_->get_all_OverlapConsequences}} @vfoas;

    #print Dumper @ocs;
    #print($vfos->{'transcript'}->{'stable_id'});
    #print("ARE WE HERE\n");
    $line->{Consequence} = join ",", keys %{{map {$_ => 0} map { $_->SO_term} @ocs}};
    #$line = $ocs[0]->$term_method || $ocs[0]->SO_term;
    my $conLine = $line->{Consequence};
    if (!defined $ocs[0]) {
      print("No overlap consequences found for this variation feature.\n");
      return $conLine, 99; # Return a high rank to filter out this record
    }
    my $rank = $ocs[0]->rank;
    #print Dumper $line;

    #push @return, $line;
    #print("$conLine\n");

  return $conLine, $rank;
}



1;