# standard libraries
import logging
from typing import Any, List


LOGGER = logging.getLogger(__name__)


def chunk_list(input_list: List[Any], chunk_size: int = 100) -> List[List[Any]]:
    """Chunks a given list into a list of lists of a specified size."""
    chunks: List[List[Any]] = [input_list[x:x + chunk_size] for x in range(0, len(input_list), chunk_size)]
    chunk_lengths: List[str] = [str(len(chunk)) for chunk in chunks]
    LOGGER.info(
        f'Chunked list of length {len(input_list)} into {len(chunks)} list(s) ' +
        f'with the following length(s): {", ".join(chunk_lengths)}'
    )
    return chunks
