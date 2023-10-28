import subprocess
import gzip 
import os
import hashlib
from subprocess import check_output

def md5_sum(fn):
    """
    Calculate the MD5 hash of a file.
    
    Args:
    - fn (str): Path to the file for which the MD5 hash is to be computed.
    
    Returns:
    - str: The MD5 hash of the file.
    """
    with open(fn, "rb") as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()

def rewrite_id(src, dst, old_id, new_id, prefix=None):
    """
    Rewrite lines in a file, replacing occurrences of an old ID with a new ID.
    An optional prefix can be specified to limit which lines are modified.
    
    Args:
    - src (str): Source file path.
    - dst (str): Destination file path.
    - old_id (str): ID to be replaced.
    - new_id (str): Replacement ID.
    - prefix (str, optional): Prefix character to determine which lines to modify. Defaults to None.
    
    Returns:
    - tuple: MD5 checksum and size (in bytes) of the modified file.
    """
    fsrc = open(src)
    fdst = open(dst, "w")
    for line in fsrc:
        if not prefix or (prefix and line[0] == prefix):
            line = line.replace(old_id, new_id)
        fdst.write(line)
    fsrc.close()
    fdst.close()
    md5 = md5_sum(dst)
    size = os.stat(dst).st_size
    return md5, size


def find_assembly_id(src):
    fsrc = open(src)
    line = fsrc.readline()
    return "_".join(line[1:].split("_")[0:-1])


def assembly_contigs(src, dst, omic_id, act_id):
    scaf = src.replace("_contigs", "_scaffolds")
    old_id = find_assembly_id(scaf)
    return rewrite_id(src, dst, old_id, act_id, prefix=">")


def assembly_scaffolds(src, dst, omic_id, act_id):
    old_id = find_assembly_id(src)
    return rewrite_id(src, dst, old_id, act_id, prefix=">")


def assembly_coverage_stats(src, dst, omic_id, act_id):
    scaf = src.replace("_covstats.txt", "_scaffolds.fna")
    old_id = find_assembly_id(scaf)
    return rewrite_id(src, dst, old_id, act_id)


def assembly_agp(src, dst, omic_id, act_id):
    scaf = src.replace("_assembly.agp", "_scaffolds.fna")
    old_id = find_assembly_id(scaf)
    return rewrite_id(src, dst, old_id, act_id)


def convert_script(script, src, dst, old_id, act_id):
    cmd = ["./rewrite_bam.sh", src, dst, old_id, act_id]
    results = check_output(cmd)
    md5 = md5_sum(dst)
    size = os.stat(dst).st_size
    return md5, size


def assembly_coverage_bam(src, dst, omic_id, act_id):
    scaf = src.replace("_pairedMapped_sorted.bam", "_scaffolds.fna")
    old_id = find_assembly_id(scaf)
    return convert_script("./rewrite_bam.sh", src, dst, old_id, act_id)


def xassembly_info_file(src, dst, omic_id, act_id):
    return []

def rewrite_bam(type, old_bam, new_bam, old_id, new_id):
    
    if type == "inside":
        print(f"Rewriting {new_bam}")

        cmd1 = ["samtools", "view", "-h", old_bam]
        cmd2 = ["sed", f"s/{old_id}/{new_id}/g"]
        cmd3 = ["samtools", "view", "-hb", "-o", ]

        # Create a pipeline: cmd1 | cmd2 | cmd3
        p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(cmd2, stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close() 
        p3 = subprocess.Popen(cmd3, stdin=p2.stdout)
        p2.stdout.close()
        p3.communicate() 

    else:
        with open(new_bam, 'w') as f:
            pass  # touch file


def rewrite_sam(input_sam, output_sam, old_id, new_id):
    
    with gzip.open(input_sam, 'rt') as f_in, gzip.open(output_sam, 'wt') as f_out:
        for line in f_in:
            f_out.write(line.replace(old_id, new_id))

