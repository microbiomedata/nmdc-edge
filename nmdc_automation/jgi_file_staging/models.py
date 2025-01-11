from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class Sample(BaseModel):
    project: str
    apGoldId: str
    studyId: str
    itsApId: str
    biosample_id: str
    seq_id: str
    file_name: str
    file_status: str
    file_size: int
    jdp_file_id: str
    md5sum: Optional[str]
    analysis_project_id: str
    create_date: datetime = datetime.now()
    update_date: Optional[datetime]
    request_id: Optional[str]


class Globus(BaseModel):
    task_id: str
    task_status: str

