import copy
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
        nucleotide_sequencing_id=nucleotide_sequencing_id, import_project_dir=base_test_dir / "import_project_dir",
        # 22 files in here
        import_yaml=yaml_file, runtime_api=mock_runtime_api
    )


@pytest.fixture
def mock_minted_ids():
    return {"data_object_ids": {"Metagenome Raw Reads": "existing_data_object_id"},
        "workflow_execution_ids": {"WorkflowA": "existing_workflow_id"}}


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
        object_type=ImportMapper.NMDC_DATA_OBJECT_TYPE, data_object_type=ImportMapper.METAGENOME_RAW_READS
    )
    assert result == "existing_data_object_id"


def test_get_or_create_minted_id_new_data_object(import_mapper_instance, mock_minted_ids, mock_runtime_api):
    import_mapper_instance.minted_ids = mock_minted_ids
    result = import_mapper_instance.get_or_create_minted_id(
        object_type=ImportMapper.NMDC_DATA_OBJECT_TYPE, data_object_type="NewDataObject"
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


def test_import_specs_by_workflow_type_returns_dict(import_mapper_instance):
    import_specs_by_workflow_type = import_mapper_instance.import_specs_by_workflow_type
    assert isinstance(import_specs_by_workflow_type, dict)


def test_file_mappings_by_data_object_type_returns_dict(import_mapper_instance):
    import_file_mappings_by_data_object_type = import_mapper_instance.file_mappings_by_data_object_type
    assert isinstance(import_file_mappings_by_data_object_type, dict)


def test_file_mappings_by_workflow_type_returns_dict(import_mapper_instance):
    import_file_mappings_by_workflow_type = import_mapper_instance.file_mappings_by_workflow_type
    assert isinstance(import_file_mappings_by_workflow_type, dict)


def test_workflow_execution_ids_returns_list(import_mapper_instance):
    import_workflow_execution_ids = import_mapper_instance.workflow_execution_ids
    assert isinstance(import_workflow_execution_ids, list)


def test_workflow_execution_types_returns_list(import_mapper_instance):
    import_workflow_execution_types = import_mapper_instance.workflow_execution_types
    assert isinstance(import_workflow_execution_types, list)


def test_update_file_mappings(import_mapper_instance):
    for fm in import_mapper_instance.file_mappings:
        assert fm.workflow_execution_id is None
        assert fm.data_object_id is None

    for fm in import_mapper_instance.file_mappings:
        import_mapper_instance.update_file_mappings(
            fm.data_object_type, data_object_id='nmdc:dobj', workflow_execution_id='nmdc:wf'
        )
    for fm in import_mapper_instance.file_mappings:
        assert fm.workflow_execution_id == 'nmdc:wf'
        assert fm.data_object_id == 'nmdc:dobj'


def test_get_nmdc_file_name(import_mapper_instance):
    # Prepare - assign workflow IDs to file mappings
    for fm in import_mapper_instance.file_mappings:
        import_mapper_instance.update_file_mappings(
            fm.data_object_type, data_object_id='nmdc:dobj', workflow_execution_id='nmdc:wf'
        )
    for fm in import_mapper_instance.file_mappings:
        nmdc_file_name = import_mapper_instance.get_nmdc_data_file_name(fm)
        assert "nmdc_wf" in nmdc_file_name


def test_get_has_input_has_output_for_workflow_type_returns_lists(import_mapper_instance):
    wfe_types = import_mapper_instance.workflow_execution_types
    for wfe_type in wfe_types:
        has_input, has_output = import_mapper_instance.get_has_input_has_output_for_workflow_type(wfe_type)
        assert isinstance(has_input, list)
        assert isinstance(has_output, list)


def test_root_directory(import_mapper_instance):
    root_dir = import_mapper_instance.root_directory
    assert root_dir == os.path.join("import_project_dir", "nmdc:omprc-11-importT")


def test_data_source_url(import_mapper_instance):
    data_source_url = import_mapper_instance.data_source_url
    assert data_source_url == "https://data.microbiomedata.org/data"


def test_file_mapping_equality(import_mapper_instance):
    for fm in import_mapper_instance.file_mappings:
        fm_copy = copy.deepcopy(fm)
        assert fm_copy == fm
