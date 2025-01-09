from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class Sample(BaseModel):
    apGoldId: str
    studyId: str
    itsApId: int
    projects: str
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
