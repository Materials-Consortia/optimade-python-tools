from io import BytesIO
from typing import Union
from pydantic import AnyUrl
from datetime import datetime, timezone
from optimade.models import EntryResponseMany, EntryResponseOne
import h5py
import numpy as np


def generate_hdf5_file_content(
    response_object: Union[EntryResponseMany, EntryResponseOne, dict, list, tuple]
) -> bytes:
    """This function generates the content of a hdf5 file from an EntryResponse object.
    It should also be able to handle python dictionaries lists and tuples."""

    temp_file = BytesIO()
    hdf5_file = h5py.File(temp_file, "w")
    if isinstance(response_object, (EntryResponseMany, EntryResponseOne)):
        response_object = response_object.dict(exclude_unset=True)
    store_hdf5_dict(hdf5_file, response_object)
    hdf5_file.close()
    file_content = temp_file.getvalue()
    temp_file.close()
    return file_content


def store_hdf5_dict(hdf5_file, iterable: Union[dict, list, tuple], group: str = ""):
    """This function stores a python list, dictionary or tuple in a hdf5 file.
    the currently supported datatypes are str, int, float, list, dict, tuple, bool, AnyUrl,
    None ,datetime or any numpy type or numpy array as long as it does not contain a numpy object.

    Parameters:
        hdf5_file: An hdf5 file like object.
        iterable: The object to be stored in the hdf5 file.
        group: This indicates to group in the hdf5 file the list, tuple or dictionary should be added.
    """
    if isinstance(iterable, (list, tuple)):
        iterable = enumerate(iterable)
    elif isinstance(iterable, dict):
        iterable = iterable.items()
    for x in iterable:
        key = str(x[0])
        value = x[1]
        if isinstance(
            value, (list, tuple)
        ):  # For now, I assume that all values in the list have the same type.
            if len(value) < 1:  # case empty list
                hdf5_file[group + "/" + key] = []
                continue
            val_type = type(value[0])
            if val_type == dict:
                hdf5_file.create_group(group + "/" + key)
                store_hdf5_dict(hdf5_file, value, group + "/" + key)
            elif val_type.__module__ == np.__name__:
                if val_type.dtype != object:
                    hdf5_file[group + "/" + key] = value
                else:
                    raise ValueError(
                        "Cannot store numpy arrays with dtype: 'object' in hdf5."
                    )
            elif isinstance(value[0], (int, float)):
                hdf5_file[group + "/" + key] = np.asarray(value)
            elif isinstance(value[0], str):
                hdf5_file[group + "/" + key] = value
            elif isinstance(value[0], (list, tuple)):
                list_type = get_recursive_type(value[0])
                if list_type in (int, float):
                    hdf5_file[group + "/" + key] = np.asarray(value)
                else:
                    hdf5_file.create_group(group + "/" + key)
                    store_hdf5_dict(hdf5_file, value, group + "/" + key)
            else:
                raise ValueError(
                    f"The list with type :{val_type} cannot be converted to hdf5."
                )
        elif isinstance(value, dict):
            hdf5_file.create_group(group + "/" + key)
            store_hdf5_dict(hdf5_file, value, group + "/" + key)
        elif isinstance(value, bool):
            hdf5_file[group + "/" + key] = np.bool_(value)
        elif isinstance(
            value, AnyUrl
        ):  # This case hat to be placed above the str case as AnyUrl inherits from the string class, but cannot be handled directly by h5py.
            hdf5_file[group + "/" + key] = str(value)
        elif isinstance(
            value,
            (
                int,
                float,
                str,
            ),
        ):
            hdf5_file[group + "/" + key] = value
        elif type(value).__module__ == np.__name__:
            if value.dtype != object:
                hdf5_file[group + "/" + key] = value
            else:
                raise ValueError(
                    "Cannot store numpy arrays with dtype: 'object' in hdf5."
                )
        elif isinstance(value, datetime):
            hdf5_file[group + "/" + key] = value.astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        elif value is None:
            hdf5_file[group + "/" + key] = h5py.Empty(
                "f"
            )  # hdf5 does not seem to have a proper null or None type.
        else:
            raise ValueError(f"Do not know how to store a value of {type(value)}")


def get_recursive_type(obj):
    if isinstance(obj, (list, tuple)):
        if len(obj) == 0:
            return None
        else:
            if isinstance(obj[0], (list, tuple)):
                return get_recursive_type(obj[0])
            else:
                return type(obj[0])
    return type(obj)


def generate_response_from_hdf5(response):
    """This function takes the content of an hdf5 file and extracts the d"""
    temp_file = BytesIO(response)
    hdf5_file = h5py.File(temp_file, "r")
    response_dict = generate_dict_from_hdf5(hdf5_file, "dict")
    return response_dict


def generate_dict_from_hdf5(hdf5_file, value_type, dict_tree="/"):
    if value_type == "dict":
        return_value = {}
        for key, value in hdf5_file[dict_tree].items():
            if isinstance(value, h5py._hl.group.Group):
                if list(value.keys())[0].isdigit():
                    new_value_type = "list"
                else:
                    new_value_type = "dict"
                return_value[key] = generate_dict_from_hdf5(
                    hdf5_file, new_value_type, dict_tree=dict_tree + key + "/"
                )
            else:
                if isinstance(value[()], h5py._hl.base.Empty):
                    return_value[key] = None
                elif isinstance(value[()], bytes):
                    return_value[key] = value[()].decode()
                else:
                    return_value[key] = value[
                        ()
                    ]  # I still have to check which other types I could get.
    if value_type == "list":
        return_value = []
        for key, value in hdf5_file[dict_tree].items():
            if isinstance(value, h5py._hl.group.Group):
                if list(value.keys())[0].isdigit():
                    new_value_type = "list"
                else:
                    new_value_type = "dict"
                return_value.append(
                    generate_dict_from_hdf5(
                        hdf5_file, new_value_type, dict_tree=dict_tree + key + "/"
                    )
                )
            else:
                if isinstance(value[()], h5py._hl.base.Empty):
                    return_value.append(None)
                elif isinstance(value[()], bytes):
                    return_value.append(value[()].decode())
                else:
                    return_value.append(
                        value[()]
                    )  # I still have to check which other types I could get.
    return return_value
