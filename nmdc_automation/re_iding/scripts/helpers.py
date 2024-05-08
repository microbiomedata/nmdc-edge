#!/usr/bin/env python3

import click
import random
import pysam


@click.group()
def cli():
    pass

@cli.command()
@click.argument("input_bam", type=click.Path(exists=True))
@click.argument("output_bam", type=click.Path())
@click.argument("subset_size", type=int)
def create_subset_bam(input_bam, output_bam, subset_size):
    with pysam.AlignmentFile(input_bam, "rb") as input_bam_file, \
            pysam.AlignmentFile(output_bam, "wb", header=input_bam_file.header) as output_bam_file:

        # Get total number of reads in the input BAM file
        total_reads = input_bam_file.count(until_eof=True)

        # Generate a random subset of read indices
        subset_indices = random.sample(range(total_reads), min(subset_size, total_reads))

        # Iterate through the input BAM file and write the selected reads to the output BAM file
        for i, read in enumerate(input_bam_file):
            if i in subset_indices:
                output_bam_file.write(read)



if __name__ == "__main__":
    cli(obj={})