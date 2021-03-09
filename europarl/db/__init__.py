from .documents import Documents
from .interface import DBInterface, create_table_structure
from .requests import Request
from .rules import Rules
from .sessionDay import SessionDay
from .tables import Table
from .url import URLs

tables = [
    Rules,
    SessionDay,
    URLs,
    Documents,
    Request,
]
