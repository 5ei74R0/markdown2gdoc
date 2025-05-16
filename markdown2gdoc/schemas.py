from typing import NewType

RequestType = NewType(
    "RequestType",
    str,
)

BatchUpdateRequest = NewType(
    "BatchUpdateRequest",
    dict[RequestType, dict],
)