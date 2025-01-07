from unittest.mock import MagicMock

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
        import_project_dir=base_test_dir / "import_project_dir",
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
    assert result == "mocked_id_for_NewWorkflow"
    assert import_mapper_instance.minted_ids["workflow_execution_ids"]["NewWorkflow"] == "mocked_id_for_NewWorkflow"


def test_get_or_create_minted_id_missing_data_object_type(import_mapper_instance):
    with pytest.raises(TypeError, match="Must specify data_object_type for a Data Object"):
        import_mapper_instance.get_or_create_minted_id(object_type=ImportMapper.NMDC_DATA_OBJECT_TYPE)

