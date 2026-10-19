import datetime as dt

from pydantic import StrictInt, StrictStr

from yt_shared.schemas.base import RealBaseModel


class CacheSchema(RealBaseModel):
    cache_id: StrictStr
    cache_unique_id: StrictStr
    file_size: StrictInt
    date_timestamp: dt.datetime
