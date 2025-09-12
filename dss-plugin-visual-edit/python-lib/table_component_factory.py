"""
Abstraction layer for generating data table column definitions for different components (Tabulator, AgGrid, etc).
"""

from typing import Any, Dict, List

# Import Tabulator-specific logic
from TabulatorColumnAdapter import get_columns_tabulator

# Future: import AgGrid-specific logic here
# from aggrid_utils import get_columns_aggrid


def get_table_columns(
    de, table_type: str = "tabulator", **kwargs
) -> List[Dict[str, Any]]:
    """
    Returns column definitions for the specified data table component.
    Args:
        de: DataEditor instance
        table_type: 'tabulator', 'aggrid', etc.
        kwargs: Additional arguments for the specific table type
    """
    if table_type == "tabulator":
        return get_columns_tabulator(de, **kwargs)
    # elif table_type == "aggrid":
    #     return get_columns_aggrid(de, **kwargs)
    else:
        raise ValueError(f"Unsupported table_type: {table_type}")
