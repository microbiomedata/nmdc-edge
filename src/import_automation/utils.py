from zipfile import ZipFile
import logging
import os

logger = logging.getLogger(__name__) 


def object_action(file_s,action,multiple=False):
    
    if action == 'none':
        return get_basename(file_s)
    elif action == 'rename':
        return rename(file_s)
    elif action == 'zip':
        if multiple == True:
            map(zip_file, file_s)
        else:
            zip_file(file_s)
    else:
        logger.error(f"No mapping action found for {file_s}")
            
 
def get_basename(file):
    
    return os.path.basename(file)
    
    
def rename(activity_id, nmdc_suffix):
    
    activity_file_id = activity_id.replace(':','_' )
    
    nmdc_file_name = activity_file_id + nmdc_suffix
    
    return nmdc_file_name

                
def zip_file(activity_id, nmdc_suffix,file,project_dir):
    '''Zip bin files'''
    
    zip_file_name = rename(activity_id, nmdc_suffix)
    
    if not os.path.exists(os.path.join(project_dir,zip_file_name)):
        with ZipFile(os.path.join(project_dir, zip_file_name), mode='w') as zipped_file:
            zipped_file.write(file)
            
    else:
        with ZipFile(os.path.join(project_dir, zip_file_name), mode='a') as zipped_file:
            zipped_file.write(file)
            
    return zip_file_name

    

def file_handler(project_dir,original_file, updated_file, destination_dir):
    try:
        os.makedirs(destination_dir)
    except FileExistsError:
        logger.debug(f'{destination_dir} already exists')
    
    original_path = os.path.join(project_dir,original_file)
    linked_path = os.path.join(destination_dir,updated_file)
    try:
        os.link(original_path, linked_path)
    except FileExistsError:
        logger.info(f'{linked_path} already exists')
        
    return linked_path
    
def file_link(import_project_dir: str,import_file: str, destination_dir: str, updated_file: str):
        
        try:
            os.makedirs(destination_dir)
        except FileExistsError:
            logger.debug(f'{destination_dir} already exists')
        
            
        original_path = os.path.join(import_project_dir,import_file)
        linked_path = os.path.join(destination_dir,updated_file)
        
        try:
            os.link(original_path, linked_path)
        except FileExistsError:
            logger.info(f'{linked_path} already exists')