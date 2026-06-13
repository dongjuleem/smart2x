"""Command-line interface for smart2x."""

import csv
import glob
import sys
from pathlib import Path

import click

from .convert import convert, UMI_LENGTH
from .whitelist import DEFAULT_KIT, WHITELISTS, list_kits, load_whitelist


@click.group()
@click.version_option()
def main():
    """smart2x — Convert Smart-seq per-cell BAMs to 10x-compatible BAM."""


@main.command("convert")
@click.argument("bam_files", nargs=-1, required=False)
@click.option("-i", "--input-dir", type=click.Path(exists=True), help="Directory containing per-cell BAM files")
@click.option("-o", "--output", required=True, type=click.Path(), help="Output BAM path (e.g. possorted_genome_bam.bam)")
@click.option("--kit", default=DEFAULT_KIT, show_default=True,
              type=click.Choice(list(WHITELISTS.keys())), help="10x kit / barcode whitelist")
@click.option("--barcode-map", type=click.Path(exists=True),
              help="TSV file with columns: cell_name<TAB>barcode (overrides whitelist auto-assign)")
@click.option("--threads", default=1, show_default=True, help="Threads for sorting")
@click.option("--tmp-dir", type=click.Path(), help="Temporary directory for intermediate files")
@click.option("--barcode-output", default="barcodes.tsv", show_default=True,
              help="Output TSV with cell→barcode mapping")
def convert_cmd(bam_files, input_dir, output, kit, barcode_map, threads, tmp_dir, barcode_output):
    """Convert Smart-seq per-cell BAMs to 10x-compatible possorted BAM.

    BAM files can be passed as arguments or via --input-dir.

    \b
    Examples:
      smart2x convert -i ./bams/ -o possorted_genome_bam.bam
      smart2x convert cell1.bam cell2.bam -o out.bam --kit 3pv2
      smart2x convert -i ./bams/ -o out.bam --barcode-map my_map.tsv
    """
    # Collect BAM files
    bams = list(bam_files)
    if input_dir:
        bams += sorted(glob.glob(str(Path(input_dir) / "*.bam")))
    if not bams:
        click.echo("Error: no BAM files provided. Use arguments or --input-dir.", err=True)
        sys.exit(1)

    click.echo(f"Found {len(bams)} BAM file(s).")

    # Determine unique cell names (use parent dir name if stems are duplicated)
    stems = [Path(b).stem for b in bams]
    if len(set(stems)) < len(stems):
        cell_names = [Path(b).parent.name for b in bams]
        click.echo("Duplicate filenames detected — using parent directory names as cell names.")
    else:
        cell_names = stems

    # Resolve barcodes
    if barcode_map:
        # Load user-provided mapping
        mapping = {}
        with open(barcode_map) as f:
            for row in csv.reader(f, delimiter="\t"):
                if len(row) >= 2:
                    mapping[row[0]] = row[1]
        barcodes = []
        for cell in cell_names:
            if cell not in mapping:
                click.echo(f"Error: cell '{cell}' not found in barcode map.", err=True)
                sys.exit(1)
            barcodes.append(mapping[cell])

    else:
        # Auto-assign from whitelist
        click.echo(f"Loading whitelist for kit '{kit}'...")
        whitelist = load_whitelist(kit)
        if len(bams) > len(whitelist):
            click.echo(
                f"Error: {len(bams)} cells exceed whitelist size ({len(whitelist)}).", err=True
            )
            sys.exit(1)
        barcodes = whitelist[: len(bams)]

    # Run conversion
    cell_barcode_map = convert(
        bam_files=bams,
        barcodes=barcodes,
        output_bam=output,
        cell_names=cell_names,
        threads=threads,
        tmp_dir=tmp_dir,
    )

    # Write barcodes.tsv (Cell Ranger format: single column, BARCODE-1)
    with open(barcode_output, "w") as f:
        for bc in cell_barcode_map.values():
            f.write(bc + "-1\n")

    click.echo(f"\nDone.")
    click.echo(f"  BAM:          {output}")
    click.echo(f"  Barcode map:  {barcode_output}")


@main.command("list-kits")
def list_kits_cmd():
    """List available 10x kits and their whitelists."""
    list_kits()


