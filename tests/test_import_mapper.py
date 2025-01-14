import os.path
from unittest.mock import MagicMock, patch

import pytest
from nmdc_automation.import_automation.import_mapper import ImportMapper


@pytest.fixture
def mock_runtime_api():
    api = MagicMock()
    api.minter = MagicMock(side_effect=lambda obj_type: f"mocked_id_for_{obj_type}")
    return api


@pytest.fixture
def import_mapper_instance(mock_runtime_api, base_test_dir):
    yaml_file = base_test_dir / "import_test.yaml"
    nucleotide_sequencing_id = "nmdc:omprc-11-importT"
    return ImportMapper(
        nucleotide_sequencing_id=nucleotide_sequencing_id,
        import_project_dir=base_test_dir / "import_project_dir",  # 22 files in here
        import_yaml=yaml_file,
        runtime_api=mock_runtime_api
    )


@pytest.fixture
def mock_minted_ids():
    return {
        "data_object_ids": {
            "Metagenome Raw Reads": "existing_data_object_id"
        },
        "workflow_execution_ids": {
            "WorkflowA": "existing_workflow_id"
        }
    }

@patch("os.listdir")
def test_import_files_initialized(mock_listdir, import_mapper_instance):
    mock_listdir.return_value = ["file1.txt", "file2.txt"]
    assert len(import_mapper_instance.file_mappings) == 22

def test_write_minted_id_file(import_mapper_instance, base_test_dir):
    import_project_dir = base_test_dir / "import_project_dir"
    nucleotide_sequencing_id = "nmdc:omprc-11-importT"
    id_file = os.path.join(import_project_dir, f"{nucleotide_sequencing_id}_minted_ids.json")
    if os.path.exists(id_file):
        os.remove(id_file)
    import_mapper_instance.write_minted_id_file()
    assert os.path.exists(id_file)



def test_get_or_create_minted_id_existing_data_object(import_mapper_instance, mock_minted_ids):
    import_mapper_instance.minted_ids = mock_minted_ids
    result = import_mapper_instance.get_or_create_minted_id(
        object_type=ImportMapper.NMDC_DATA_OBJECT_TYPE,
        data_object_type=ImportMapper.METAGENOME_RAW_READS
    )
    assert result == "existing_data_object_id"


def test_get_or_create_minted_id_new_data_object(import_mapper_instance, mock_minted_ids, mock_runtime_api):
    import_mapper_instance.minted_ids = mock_minted_ids
    result = import_mapper_instance.get_or_create_minted_id(
        object_type=ImportMapper.NMDC_DATA_OBJECT_TYPE,
        data_object_type="NewDataObject"
    )
    assert result == "mocked_id_for_nmdc:DataObject"
    assert import_mapper_instance.minted_ids["data_object_ids"]["NewDataObject"] == "mocked_id_for_nmdc:DataObject"


def test_get_or_create_minted_id_existing_workflow(import_mapper_instance, mock_minted_ids):
    import_mapper_instance.minted_ids = mock_minted_ids
    result = import_mapper_instance.get_or_create_minted_id(
        object_type="WorkflowA"
    )
    assert result == "existing_workflow_id"


def test_get_or_create_minted_id_new_workflow(import_mapper_instance, mock_minted_ids, mock_runtime_api):
    import_mapper_instance.minted_ids = mock_minted_ids
    result = import_mapper_instance.get_or_create_minted_id(
        object_type="NewWorkflow"
    )
    assert result == "mocked_id_for_NewWorkflow.1"
    assert import_mapper_instance.minted_ids["workflow_execution_ids"]["NewWorkflow"] == "mocked_id_for_NewWorkflow.1"


def test_get_or_create_minted_id_missing_data_object_type(import_mapper_instance):
    with pytest.raises(TypeError, match="Must specify data_object_type for a Data Object"):
        import_mapper_instance.get_or_create_minted_id(object_type=ImportMapper.NMDC_DATA_OBJECT_TYPE)

def test_import_specifications_returns_dict(import_mapper_instance):
    import_specifications = import_mapper_instance.import_specifications
    assert isinstance(import_specifications, dict)

def test_import_specifications_loads_yaml_correctly(import_mapper_instance, tmp_path):
    yaml_content = """
    key1: value1
    key2: value2
    """
    yaml_file = tmp_path / "import_specifications.yaml"
    yaml_file.write_text(yaml_content)
    import_mapper_instance.import_yaml = str(yaml_file)
    import_specifications = import_mapper_instance.import_specifications
    assert import_specifications == {"key1": "value1", "key2": "value2"}

def test_import_specifications_with_invalid_yaml(import_mapper_instance, tmp_path):
    invalid_yaml_content = "invalid_yaml: [unmatched_bracket"
    yaml_file = tmp_path / "import_specifications.yaml"
    yaml_file.write_text(invalid_yaml_content)
    import_mapper_instance.import_yaml = str(yaml_file)
    with pytest.raises(Exception):
        _ = import_mapper_instance.import_specifications

def test_root_directory(import_mapper_instance):
    root_dir = import_mapper_instance.root_directory
    assert root_dir == os.path.join("import_project_dir", "nmdc:omprc-11-importT")

def test_data_source_url(import_mapper_instance):
    data_source_url = import_mapper_instance.data_source_url
    assert data_source_url == "https://data.microbiomedata.org/data"

