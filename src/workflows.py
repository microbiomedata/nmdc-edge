from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


def load_workflows(yaml_file):
    workflows = []
    data = load(open(yaml_file), Loader)
    for wf in data["Workflows"]:
        workflows.append(Workflow(wf))
    return workflows


_FIELDS = ["Name",
           "Type",
           "Enabled",
           "Git_repo",
           "Version",
           "WDL",
           "Collection",
           "Predecessor",
           "Input_prefix",
           "Inputs",
           "Activity",
           "Outputs"
           ]


class Workflow():
    def __init__(self, wf: dict):
        for f in _FIELDS:
            attr_name = f.lower().replace(" ", "_")
            setattr(self, attr_name, wf[f])
    #   - output: filtered_final
    #     name: Reads QC result fastq (clean data)
    #     suffix: "_filtered.fastq.gz"
    #     data_object_type: Filtered Sequencing Reads
    #     description: "Reads QC for {id}"


if __name__ == "__main__":
    load_workflows("workflows.yaml")
