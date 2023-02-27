import logging
from .workflows import Workflow


def load_activities(db, workflows: Workflow, filter={}):
    acts = Activites(db, workflows, filter=filter)
    acts_by_wf = dict()
    for wf in workflows:
        acts_by_wf[wf] = []
    for act in acts.activities:
        acts_by_wf[act.workflow].append(act)
    return acts_by_wf


class Activites():
    def __init__(self, db, workflows: Workflow, filter={}):
        # Build up a filter of what types are used
        required_types = set()
        for wf in workflows:
            required_types.update(set(wf.do_types))

        # This is map from the do ID to the activity
        # that created it.
        data_obj_act = dict()
        data_objs_by_id = dict()
        for rec in db.data_object_set.find():
            do = DataObject(rec)
            if do.data_object_type not in required_types:
                continue
            data_objs_by_id[do.id] = do

        # Build up a set of relevant activities and a map from
        # the output objects to the activity that generated them.
        activities = []
        for wf in workflows:
            q = filter
            q['git_url'] = wf.git_repo
            q['version'] = wf.version
            for rec in db[wf.collection].find(q):
                act = Activity(rec, wf)
                for do_id in act.has_output:
                    if do_id in data_objs_by_id:
                        do = data_objs_by_id[do_id]
                        act.add_data_object(do)
                    # If its a dupe, set it to none
                    # so we can ignore it later.
                    # Once we re-id the data objects this
                    # shouldn't happen
                    if do_id in data_obj_act:
                        logging.warning(f"Duplicate output object {do_id}")
                        data_obj_act[do_id] = None
                    else:
                        data_obj_act[do_id] = act
                activities.append(act)

        # We now have a list of all the activites and
        # a map of all of the data objects they generated.
        # Let's use this to find the parent activity
        # for each child activity
        for act in activities:
            act_pred_wfs = act.workflow.parents
            if not act_pred_wfs:
                continue
            # Go through its inputs
            for do_id in act.has_input:
                if do_id not in data_obj_act:
                    # This really shouldn't happen
                    logging.warning(f"Missing data object {do_id}")
                    continue
                parent_act = data_obj_act[do_id]
                # This is to cover the case where it was a duplicate.
                # This shouldn't happen in the future.
                if not parent_act:
                    logging.warning("Parent act is none")
                    continue
                # Let's make sure these came from the same source
                # This is just a safeguard
                if act.was_informed_by != parent_act.was_informed_by:
                    logging.warning("Mismatched informed by found for"
                                    f"{do_id} in {act.id} ({act.name})")
                    continue
                # We only want to use it as a parent if it is the right
                # parent workflow. Some inputs may come from ancestors
                # further up
                if parent_act.workflow in act_pred_wfs:
                    # This is the one
                    act.parent = parent_act
                    parent_act.children.append(act)
                    break
            if len(act.workflow.parents) > 0 and not act.parent:
                logging.warning("Didn't find a parent for "
                                f"{act.id} ({act.name}) {act.workflow.name}")
        # Now all the activities have their parent
        self.activities = activities


class DataObject(object):
    _FIELDS = [
        "id",
        "name",
        "description",
        "url",
        "md5_checksum",
        "file_size_bytes",
        "data_object_type"
    ]

    def __init__(self, rec: dict):
        for f in self._FIELDS:
            setattr(self, f, rec.get(f))


class Activity(object):
    _FIELDS = [
        "id",
        "name",
        "git_url",
        "version",
        "has_input",
        "has_output",
        "was_informed_by",
    ]
    parent = None
    children = []
    data_objects_by_type = dict()

    def __init__(self, activity_rec: dict, wf):
        self.workflow = wf
        for f in self._FIELDS:
            setattr(self, f, activity_rec[f])

    def add_data_object(self, do: DataObject):
        self.data_objects_by_type[do.data_object_type] = do
