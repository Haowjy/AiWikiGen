# generated by datamodel-codegen:
#   filename:  thing_schema.json
#   timestamp: 2024-10-15T01:41:53+00:00

from __future__ import annotations

from typing import List, Optional
import jsonref

from pydantic import BaseModel, Field

class Description(BaseModel):
    appearance: str = Field(..., description='Physical description of the object')
    properties: Optional[str] = Field(
        None, description='Special properties, functions, or capabilities of the object'
    )

class RelatedEntity(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    relation: Optional[str] = None
    description: Optional[str] = None

class ThingModel(BaseModel):
    class Config:
        extra = 'forbid'

    name: str = Field(..., description='The primary name or identifier of the object')
    item_type: str = Field(
        ...,
        description='The category or type of the object (e.g., weapon, artifact, technology)',
    )
    aliases: Optional[List[str]] = Field(
        None, description='Alternative names or identifiers for the object'
    )
    overview: str = Field(
        ...,
        description='A concise summary of the object, including its key features and general importance',
    )
    significance: str = Field(
        ...,
        description="The object's importance to the plot and how it impacts the story",
    )
    description: Optional[Description] = None
    background: Optional[str] = Field(
        None,
        description='Detailed description of origin, past uses, and significant events involving the object. For longer descriptions, use markdown with headers and subheaders to organize.',
    )
    current_status: Optional[str] = Field(
        None, description='The current state, location, or possessor of the object'
    )
    related_entities: Optional[List[RelatedEntity]] = Field(
        None,
        description='Characters, locations, or other entities closely associated with the object',
    )
    
    def to_json_schema():
        ret = jsonref.replace_refs(super().model_json_schema(), proxies=False)
        del ret['$defs']
        return ret
