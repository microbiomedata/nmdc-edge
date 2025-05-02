from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Sample(BaseModel):
    apGoldId: str
    studyId: str
    itsApId: int
    projects: list
    biosample_id: str
    seq_id: str
    file_name: str
    file_status: str
    file_size: int
    jdp_file_id: str
    md5sum: Optional[str] = None
    analysis_project_id: str
    create_date: datetime = datetime.now()
    update_date: Optional[datetime] = None
    request_id: Optional[str] = None


class Globus(BaseModel):
    task_id: str
    task_status: str


class SequencingProject(BaseModel):
    project_name: str
    proposal_id: str
    nmdc_study_id: str
    analysis_projects_dir: str
