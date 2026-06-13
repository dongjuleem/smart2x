"""Core BAM conversion logic: Smart-seq per-cell BAMs → 10x-compatible BAM."""

import os
import random
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import pysam
from tqdm import tqdm

UMI_LENGTH = 12  # 10x v3 UMI length


def _random_umi(length: int = UMI_LENGTH) -> str:
    return "".join(random.choices("ACGT", k=length))


def _dummy_quality(length: int) -> str:
    return "I" * length  # Phred 40


def tag_cell_bam(
    input_bam: str,
    output_bam: str,
    barcode: str,
    umi_length: int = UMI_LENGTH,
) -> int:
    """Add CB/CR/UB/UR tags to all reads in a single-cell BAM. Returns read count."""
    bc_qual = _dummy_quality(len(barcode))
    read_count = 0

    with pysam.AlignmentFile(input_bam, "rb") as inbam, \
         pysam.AlignmentFile(output_bam, "wb", header=inbam.header) as outbam:

        for read in inbam:
            umi = _random_umi(umi_length)
            umi_qual = _dummy_quality(umi_length)

            read.set_tag("CR", barcode)   # cell barcode raw
            read.set_tag("CB", barcode)   # cell barcode corrected
            read.set_tag("CY", bc_qual)   # cell barcode quality
            read.set_tag("UR", umi)       # UMI raw
            read.set_tag("UB", umi)       # UMI corrected
            read.set_tag("UY", umi_qual)  # UMI quality
            read.set_tag("xf", 25)        # 10x extra flags (valid cell + valid UMI)

            outbam.write(read)
            read_count += 1

    return read_count


def merge_and_sort(
    tagged_bams: List[str],
    output_bam: str,
    threads: int = 1,
    tmp_dir: Optional[str] = None,
) -> None:
    """Merge tagged BAMs and coordinate-sort into final output."""
    tmp = tmp_dir or tempfile.mkdtemp()
    merged_path = os.path.join(tmp, "merged_unsorted.bam")

    pysam.merge("-f", merged_path, *tagged_bams, catch_stdout=False)
    pysam.sort(
        "-o", output_bam,
        "-@", str(threads),
        merged_path,
        catch_stdout=False,
    )
    pysam.index(output_bam, catch_stdout=False)

    os.unlink(merged_path)


def convert(
    bam_files: List[str],
    barcodes: List[str],
    output_bam: str,
    cell_names: Optional[List[str]] = None,
    umi_length: int = UMI_LENGTH,
    threads: int = 1,
    tmp_dir: Optional[str] = None,
) -> Dict[str, str]:
    """
    Convert per-cell BAMs to a single 10x-compatible BAM.

    Returns: mapping of cell_name → assigned_barcode
    """
    if len(bam_files) != len(barcodes):
        raise ValueError(
            f"Number of BAM files ({len(bam_files)}) must match barcodes ({len(barcodes)})"
        )

    tmp = tmp_dir or tempfile.mkdtemp()
    tagged_bams = []
    cell_barcode_map = {}

    print(f"Tagging {len(bam_files)} cells...")
    for i, (bam_path, barcode) in enumerate(tqdm(zip(bam_files, barcodes), total=len(bam_files))):
        cell_name = cell_names[i] if cell_names else Path(bam_path).stem
        tagged_path = os.path.join(tmp, f"{i}_{cell_name}_tagged.bam")

        tag_cell_bam(bam_path, tagged_path, barcode, umi_length)
        tagged_bams.append(tagged_path)
        cell_barcode_map[cell_name] = barcode

    print("Merging and sorting...")
    merge_and_sort(tagged_bams, output_bam, threads=threads, tmp_dir=tmp)

    # Cleanup tagged BAMs
    for path in tagged_bams:
        if os.path.exists(path):
            os.unlink(path)

    return cell_barcode_map
