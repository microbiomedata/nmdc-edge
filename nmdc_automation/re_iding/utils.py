import subprocess
import gzip 

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

