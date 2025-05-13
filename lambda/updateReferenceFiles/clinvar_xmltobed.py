from collections import Counter, namedtuple
from enum import Enum
import sys
import xml.etree.ElementTree as ET


class Classification(Enum):
    GERMLINE = "Germline"
    SOMATIC = "Somatic - Clinical impact"
    ONCOGENICITY = "Somatic - Oncogenicity"


def report(x, **kwargs):
    print(ET.tostring(x).decode(), **kwargs)


def notabs(input_string):
    return input_string.replace("\t", " ")


RSV = namedtuple(
    "RSV",
    [
        "classification",
        "conditions",
        "clin_sig",
        "review_status",
        "last_evaluated",
        "accession",
    ],
)


def fast_iter(context, func, *args, **kwargs):
    root_elem = None
    for event, elem in context:
        if elem.tag == "ClinVarVariationRelease":
            root_elem = elem
            continue
        elif elem.tag != "VariationArchive" or event != "end":
            continue
        try:
            func(elem, *args, **kwargs)
        except Exception as e:
            report(elem, file=sys.stderr)
            raise e
        # It's safe to call clear() here because no descendants will be
        # accessed
        elem.clear()
        # Delete the element entirely
        root_elem.remove(elem)


def print_bed_lines(child, skipped, processed_produced):
    variation_id = child.attrib["VariationID"]
    var_name = child.attrib["VariationName"]
    classified_record = child.find("ClassifiedRecord")
    if classified_record is None:
        # We could use this instead, but then the germline_classification is broken
        classified_record = child.find("IncludedRecord")
        skipped["missing_ClassifiedRecord"] += 1
        return
    simple_allele = classified_record.find("SimpleAllele")
    try:
        location = (
            simple_allele.find("Location")
            .find('SequenceLocation[@Assembly="GRCh38"]')
            .attrib
        )
    except AttributeError:
        skipped["no_GRCh38"] += 1
        return
    try:
        ref = location["referenceAlleleVCF"]
    except KeyError as e:
        skipped["Structural"] += 1
        return
    # Just to keep this as a valid bed file
    start = int(location["positionVCF"]) - 1
    end = int(start) + len(ref)
    try:
        omim_id = simple_allele.find("XRefList").find('XRef[@DB="OMIM"]').attrib["ID"]
    except AttributeError as e:
        omim_id = "-"
    try:
        rs_id = child.find('.//XRef[@DB="dbSNP"]').attrib["ID"]
        if not rs_id.startswith("rs"):
            rs_id = f"rs{rs_id}"
    except AttributeError as e:
        rs_id = "-"
    rsv_tuples = []
    pubmed = (
        ",".join(
            {citation.text for citation in child.findall('.//ID[@Source="PubMed"]')}
        )
        or "-"
    )
    rsvs = classified_record.find("RCVList").findall("RCVAccession")
    for rsv in rsvs:
        accession = rsv.attrib["Accession"]
        conditions = ", ".join(
            condition.text
            for condition in rsv.find("ClassifiedConditionList").findall(
                "ClassifiedCondition"
            )
        )
        base_classification = rsv.find("RCVClassifications")
        classification = base_classification.find("GermlineClassification")
        if (
            classification := base_classification.find("GermlineClassification")
        ) is not None:
            classification_type = Classification.GERMLINE
        elif (
            classification := base_classification.find("SomaticClinicalImpact")
        ) is not None:
            classification_type = Classification.SOMATIC
        elif (
            classification := base_classification.find("OncogenicityClassification")
        ) is not None:
            classification_type = Classification.ONCOGENICITY
        else:
            raise Exception("Unexpected classification")
        description = classification.find("Description")
        clin_sigs = []
        last_evaluated = "-"
        # Sometimes an RCV may contain several descriptions with different significances
        for description in classification.findall("Description"):
            if classification_type in (
                Classification.GERMLINE,
                Classification.ONCOGENICITY,
            ):
                this_clin_sig = description.text
            elif classification_type == Classification.SOMATIC:
                description_attribs = description.attrib
                this_clin_sig = " - ".join(
                    s
                    for s in (
                        description.text,
                        description_attribs.get("ClinicalImpactAssertionType"),
                        description_attribs.get("ClinicalImpactClinicalSignificance"),
                    )
                    if s
                )
            clin_sigs.append(this_clin_sig)
            last_evaluated = max(
                last_evaluated, description.attrib.get("DateLastEvaluated", "-")
            )
        clin_sig = ", ".join(clin_sigs)
        review_status = classification.find("ReviewStatus").text
        rsv_tuples.append(
            RSV(
                classification=classification_type.value,
                conditions=notabs(conditions),
                clin_sig=notabs(clin_sig),
                review_status=notabs(review_status),
                last_evaluated=last_evaluated,
                accession=accession,
            )
        )
    try:
        print(
            "\n".join(
                "\t".join(
                    (
                        location["Chr"],
                        str(start),
                        str(end),
                        ref,
                        location["alternateAlleleVCF"],
                        variation_id,
                        var_name,
                        rs_id,
                        omim_id,
                        rsv.classification,
                        rsv.conditions,
                        rsv.clin_sig,
                        rsv.review_status,
                        rsv.last_evaluated,
                        rsv.accession,
                        pubmed,
                    )
                )
                for rsv in rsv_tuples
            )
        )
    except KeyError as e:
        skipped["missing_chr_or_alt"] += 1
        return
    processed_produced[0] += 1
    processed_produced[1] += len(rsv_tuples)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        in_xml = sys.argv[1]
        print(f"parsing {in_xml}", file=sys.stderr)
    else:
        in_xml = sys.stdin
        print("parsing from stdin", file=sys.stderr)
    iter_tree = ET.iterparse(in_xml, events=("start", "end"))
    skipped_records = Counter()
    processed_produced_records = [0, 0]
    fast_iter(iter_tree, print_bed_lines, skipped_records, processed_produced_records)
    print(f"{processed_produced_records=}, {skipped_records=}", file=sys.stderr)
