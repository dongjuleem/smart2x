## smart2x

Convert Smart-seq per-cell BAM files into 10x Chromium-compatible BAM format (`possorted_genome_bam.bam`).

## Installation

```bash
git clone https://github.com/djleem/smart2x.git
cd smart2x
pip install -e .
```

## Usage

### From separate directories

```bash
smart2x convert \
    cell1/Aligned.sortedByCoord.out.bam \
    cell2/Aligned.sortedByCoord.out.bam \
    cell3/Aligned.sortedByCoord.out.bam \
    -o possorted_genome_bam.bam
```

### From a single directory

```bash
smart2x convert -i ./per_cell_bams/ -o possorted_genome_bam.bam
```

### List available kits

```bash
smart2x list-kits
```

## Output

| File | Description |
|------|-------------|
| `possorted_genome_bam.bam` | 10x compatible BAM with CB, UB, and xf tags |
| `barcodes.tsv` | Cell barcodes |
