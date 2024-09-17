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
1. Get list of biosample_id's and the proposal_id for project from gold.jgi.doe.gov
2. Create CSV file with biosample ID's
3. Set options in config.ini
4. Activate pipenv
5. Get offline token https://gold-ws.jgi.doe.gov/ and export as an environment variable
6. Set environment variables for database (`source mongo_env`)
7. Run `jgi_file_metadata.py` with config.ini, the CSV with biosample ID's, the proposal ID and the project name
8. Get JDP_TOKEN 
   1. login to https://data.jgi.doe.gov/
   2. Click on profile icon in upper right corner and select 'Copy My Session Token'
9. Run `file_restoration.py` with project name and config.ini to restore files from tape
   1. 750 samples per request
   2. maximum of 10TB can be requested every 24 hours
   3. run every 24 hours until all files have been requested
10. Run `globus_file_transfer.py` after files have been restored from tape with config.ini and project name
    1. call with '--request_id' to get the Globus manifest file 
    2. If running from local machine: 
       1. copy Globus manifest file to local machine
       2. update nersc_manifests_directory to directory with manifest files
    3. call without any optional arguments to create and submit Globus batch files to perform Globus transfers