from pydantic import BaseModel


class QueryType(BaseModel):
    query_type: str


class JobPosition(BaseModel):
    job_position: str


class Location(BaseModel):
    location: str
