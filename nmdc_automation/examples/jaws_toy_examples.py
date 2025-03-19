#jaws client intalled with 'pip install --target /global/cfs/cdirs/m3408/users/nmdcda  jaws-client --index-url https://code.jgi.doe.gov/api/v4/projects/312/packages/pypi/simple'

from jaws_client import api
from jaws_client.config import Configuration
config = Configuration('/global/cfs/cdirs/m3408/jaws-install/jaws-client/nmdc-prod/jaws-prod.conf', '/global/u2/n/nmdcda/jaws.conf')
jaws = api.JawsApi(config)
import os
os.environ["JAWS_USER_CONFIG"] = "/global/u2/n/nmdcda/jaws.conf"
os.environ["JAWS_CLIENT_CONFIG"] = "/global/cfs/cdirs/m3408/jaws-install/jaws-client/nmdc-prod/jaws-prod.conf"
os.environ["PYTHONPATH"] += os.pathsep + "/global/cfs/cdirs/m3408/users/nmdcda"
#submits a JAWS job, returns a dict with the jaws job ID
response=jaws.submit(wdl_file="/my/awesome/wdl/shortReadsqc.wdl", inputs="/my/input/BMI_HCNKKBGX5_Plate4WellF4_R1.fastq.gz_inputs.json", site="nmdc")
print(response)

#example response from jaws.submit
example_response_job_dict={'run_id': 79354}

#example of parsing the job ID from the response dict
for key,job_id in example_response_job_dict.items():
    print(job_id)

#example of checking on a job that has been submitted
s_response=jaws.status("79362",verbose=False)
print(s_response)
