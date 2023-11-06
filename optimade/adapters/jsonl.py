from io import BufferedReader, BytesIO
from pathlib import Path
from typing import Union

from jsonlines import Reader, Writer

from optimade.models.partial_data import PartialDataResource


def to_jsonl(input_data: Union[list[dict], PartialDataResource]) -> bytes:
    """This function convert a list of dictionaries to the JSONL format which can be sent back in an OPTIMADE partial data response"""
    temp_file = BytesIO()
    writer = Writer(temp_file)
    if isinstance(input_data, PartialDataResource):
        writer.write(input_data.header)
        input_data = input_data.data
    if isinstance(input_data, list):
        writer.write_all(input_data)
    else:
        writer.write(input_data)
    writer.close()
    file_content = temp_file.getvalue()
    temp_file.close()
    return file_content


def from_jsonl(
    jsonl_input: Union[Path, str, bytes]
) -> Union[list, PartialDataResource]:
    if isinstance(jsonl_input, (Path, str)):
        fp: Union[BytesIO, BufferedReader] = open(jsonl_input, "rb")
    else:
        fp = BytesIO(jsonl_input)
    decoded = []
    reader = Reader(fp)
    for obj in reader:
        decoded.append(
            obj
        )  # Appending is slow, so it would be better to use a more efficient method
    reader.close()
    fp.close()
    return decoded
