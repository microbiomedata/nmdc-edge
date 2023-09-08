### JGI Data Staging

1. jgi_file_metadata.py 
   1. Get sample metadata from JGI and enter into mongodb 
2. file_restoration.py 
   1. Restore files from tape
   2. repeat until all files restored
   3. Monitor restore requests until they are fulfilled
3. globus_file_transfer.py
   1. Get Globus manifests for restored files
   2. Create and submit Globus batch file
   3. Monitor Globus transfers until complete

Config file contains parameters that can change, such as Globus id, 
notification email, file destination, etc.

Mongodb is used to track the metadata and the status of the files.

SOP
1. Get offline token https://gold-ws.jgi.doe.gov/
2. Get list of biosample_id's and proposal_id for project from gold.jgi.doe.gov
3. Get analysis projects from project proposal id
	1. https://gold-ws.jgi.doe.gov/api/v1/analysis_projects?itsProposalId={proposal_id}
4. For each sample, get the sequencing project id 
5. Use that to get analysis project id
6. For each analysis project and each organism for that project, get the list of files and the agg_id for that organism
7. Do a join for this list with the  on the agg_id and analysis project id