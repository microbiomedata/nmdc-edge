### JGI Data Staging

1. Get sample metadata from JGI and enter into mongodb
2. Restore files from tape 
   1. repeat until all files restored
   2. Monitor restore requests until they are fulfilled
3. Get Globus manifests for restored files
4. Create and submit Globus batch file
5. Monitor Globus transfers until complete

Config file contains parameters that can change, such as Globus id, 
notification email, file destination, etc.