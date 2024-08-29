import os
import json
import argparse

from mongo import get_mongo_db


from nmdc_task_log import create_task_list_df


def get_failed_tasks(project: str, archive_dir: str):

    mdb = get_mongo_db()
    workflow_id = mdb.cromwelljobs.find_one({'project': project})

    task_df = create_task_list_df(workflow_id['id'], archive_dir)
    task_df = task_df.loc[task_df.status == 'Failed']

    failed_log = os.path.join(archive_dir, 'failed_log.json')

    if task_df.empty:
        with open(failed_log, 'w') as f:
            json.dump("no failed tasks", f, indent=4)
        return

    error_list = []

    for index, row in task_df.iterrows():
        executions_dir = '/'.join(row['stderr'].split('/')[:-1])

        try:
            with open(os.path.join(executions_dir, 'stderr'), 'r') as f:
                doc = f.read()
            with open(os.path.join(executions_dir, 'stdout'), 'r') as f:
                stdout_doc = f.read()

            error_dict = {
                "task": row.task,
                "stderr": '\n'.join(doc.split('\n')[-100:]),
                "stdout": '\n'.join(stdout_doc.split('\n')[-100:])
            }
            error_list.append(error_dict)

        except FileNotFoundError:
            try:
                with open(os.path.join(executions_dir, 'stderr.background'), 'r') as f:
                    doc = f.read()
                with open(os.path.join(executions_dir, 'stdout.background'), 'r') as f:
                    stdout_doc = f.read()

                error_dict = {
                    "task": row.task,
                    "stderr": '\n'.join(doc.split('\n')[-100:]),
                    "stdout": '\n'.join(stdout_doc.split('\n')[-100:])
                }
                error_list.append(error_dict)

            except FileNotFoundError:
                error_dict = {
                    "task": row.task,
                    "stderr": "No stderr available",
                    "stdout": "No stdout available"
                }
                error_list.append(error_dict)

    with open(failed_log, 'w') as f:
        json.dump(error_list, f, indent=4)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('archive_dir', help='directory to save stderr and stdout',
                        default='/expanse/projects/nmdc/cromwell/archive')
    parser.add_argument('project', help='project code')
    args = vars((parser.parse_args()))

    get_failed_tasks(args['project'], args['archive_dir'])
