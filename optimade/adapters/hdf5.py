from io import BytesIO
from typing import Union, Any
from pydantic import AnyUrl
from datetime import datetime, timezone
from optimade.models import EntryResponseMany, EntryResponseOne
import h5py
import numpy as np


"""This adaptor class can be used to generate a hdf5 response instead of a json response and to convert the hdf5 response back into an python dictionary.
It can handle numeric data in a binary format compatible with numpy.
It is therefore more efficient than the JSON format at returning large amounts of numeric data.
It however also has more overhead resulting in a larger response for entries with little numeric data.
To enable support for your server the parameter "enabled_response_formats" can be specified in the config file.
It is a list of the supported response_formats. To support the hdf5 return format it should be set to: ["json", "hdf5"]
(support for the JSON format is mandatory)

Unfortunately, h5py does not support storing objects with the numpy.object type.
It is therefore not possible to directly store a list of dictionaries in a hdf5 file with h5py.
As a workaround, the index of a value in a list is used as a dictionary key so a list can be stored as a dictionary if neccesary.
"""


def generate_hdf5_file_content(
    response_object: Union[EntryResponseMany, EntryResponseOne, dict, list, tuple]
) -> bytes:
    """This function generates the content of a hdf5 file from an EntryResponse object.
    It should also be able to handle python dictionaries lists and tuples.

    Parameters:
        response_object: an OPTIMADE response object. This can be of any OPTIMADE entry type, such as structure,
        reference etc.

    Returns:
        A binary object containing the contents of the hdf5 file.
    """

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
    None ,datetime or any numpy type or numpy array.

    Unfortunately, h5py does not support storing objects with the numpy.object type.
    It is therefore not possible to directly store a list of dictionaries in a hdf5 file with h5py.
    As a workaround, the index of a value in a list is used as a dictionary key so a list can be stored as a dictionary if neccesary.

    Parameters:
        hdf5_file: An hdf5 file like object.
        iterable: The object to be stored in the hdf5 file.
        group: This indicates to group in the hdf5 file the list, tuple or dictionary should be added.

    Raises:
        TypeError: If this function encounters an object with a type that it cannot convert to the hdf5 format
                    a ValueError is raised.
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
                try:
                    hdf5_file[group + "/" + key] = value
                except (TypeError) as hdf5_error:
                    raise TypeError(
                        "Unfortunatly more complex numpy types like object can not yet be stored in hdf5. Error from hdf5:"
                        + hdf5_error
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
        ):  # This case had to be placed above the str case as AnyUrl inherits from the string class, but cannot be handled directly by h5py.
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
            try:
                hdf5_file[group + "/" + key] = value
            except (TypeError) as hdf5_error:
                raise TypeError(
                    "Unfortunatly more complex numpy types like object can not yet be stored in hdf5. Error from hdf5:"
                    + hdf5_error
                )
        elif isinstance(value, datetime):
            hdf5_file[group + "/" + key] = value.astimezone(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        elif value is None:
            hdf5_file[group + "/" + key] = h5py.Empty("f")
        else:
            raise ValueError(
                f"Unable to store a value of type: {type(value)} in hdf5 format."
            )


def get_recursive_type(obj: Any) -> type:
    """If obj is a list or tuple this function returns the type of the first object in the list/tuple that is not a list
    or tuple. If the list or tuple is empty it returns None.
    Finally if the object is not a list or tuple it returns the type of the object.

    Parameters:
        obj: any python object

    Returns:
        The type of the objects that the object contains or the type of the object itself when it does not contain other objects."""

    if isinstance(obj, (list, tuple)):
        if len(obj) == 0:
            return None
        else:
            if isinstance(obj[0], (list, tuple)):
                return get_recursive_type(obj[0])
            else:
                return type(obj[0])
    return type(obj)


def generate_response_from_hdf5(hdf5_content: bytes) -> dict:
    """Generates a response_dict from a HDF5 file like object.
    It is similar to the response_dict generated from the JSON response, except that the numerical data will have numpy
    types.

    Parameters:
         hdf5_content(bytes): the content of a hdf5 file.

    Returns:
         A dictionary containing the data of the hdf5 file."""

    temp_file = BytesIO(hdf5_content)
    hdf5_file = h5py.File(temp_file, "r")
    response_dict = generate_dict_from_hdf5(hdf5_file)
    return response_dict


def generate_dict_from_hdf5(
    hdf5_file: h5py._hl.files.File, group: str = "/"
) -> Union[dict, list]:
    """This function returns the content of a hdf5 group.
    Because of the workaround described under the store_hdf5_dict function, groups which have numbers as keys will be turned to lists(No guartee that the order is the same as in th eoriginal list).
    Otherwise, the group will be turned into a dict.

    Parameters:
        hdf5_file: An HDF5_object containing the data that should be converted to a dictionary or list.
        group: The hdf5 group for which the dictionary should be created. The default is "/" which will return all the data in the hdf5_object

    Returns:
        A dict or list containing the content of the hdf5 group.
    """

    return_value = None
    for key, value in hdf5_file[group].items():
        if key.isdigit():
            if return_value is None:
                return_value = []
            if isinstance(value, h5py._hl.group.Group):
                return_value.append(
                    generate_dict_from_hdf5(hdf5_file, group=group + key + "/")
                )
            elif isinstance(value[()], h5py._hl.base.Empty):
                return_value.append(None)
            elif isinstance(value[()], bytes):
                return_value.append(value[()].decode())
            else:
                return_value.append(value[()])

        else:  # Case dictionary
            if return_value is None:
                return_value = {}
            if isinstance(value, h5py._hl.group.Group):
                return_value[key] = generate_dict_from_hdf5(
                    hdf5_file, group=group + key + "/"
                )
            elif isinstance(value[()], h5py._hl.base.Empty):
                return_value[key] = None
            elif isinstance(value[()], bytes):
                return_value[key] = value[()].decode()
            else:
                return_value[key] = value[()]

    return return_value
