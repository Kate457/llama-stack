# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the terms described in the LICENSE file in
# the root directory of this source tree.

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from llama_models.schema_utils import json_schema_type, webmethod
from pydantic import BaseModel, Field


@json_schema_type
class DatasetColumnType(Enum):
    dialog = "dialog"
    text = "text"
    media = "media"
    number = "number"
    json = "json"


class DatasetDef(BaseModel):
    identifier: str = Field(
        description="A unique name for the dataset",
    )
    columns: Dict[str, DatasetColumnType]
    content_url: URL
    storage_format: str
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Any additional metadata for the dataset",
    )


@json_schema_type
class DatasetDefWithProvider(DatasetDef):
    provider_id: str = Field(
        description="ID of the provider which serves this dataset",
    )


@runtime_checkable
class Datasets(Protocol):
    @webmethod(route="/datasets/list", method="GET")
    async def list_datasets(self) -> List[DatasetDefWithProvider]: ...

    @webmethod(route="/datasets/get", method="GET")
    async def get_dataset(
        self, identifier: str
    ) -> Optional[DatasetDefWithProvider]: ...

    @webmethod(route="/datasets/register", method="POST")
    async def register_dataset(self, model: DatasetDefWithProvider) -> None: ...
