# pylint: disable=invalid-name
from typing import List, Tuple, Iterable

from optimade.models.structures import Vector3D

try:
    import numpy as np
except ImportError:
    from warnings import warn

    np = None
    NUMPY_NOT_FOUND = "NumPy not found, cannot convert structure to your desired format"


def scaled_cell(
    cell: Tuple[Vector3D, Vector3D, Vector3D]
) -> Tuple[Vector3D, Vector3D, Vector3D]:
    """Return a scaled 3x3 cell from cartesian 3x3 cell (`lattice_vectors`)

    This is based on PDB's method of calculating SCALE from CRYST data.
    For more info, see https://www.wwpdb.org/documentation/file-format-content/format33/sect8.html#SCALEn
    """
    if globals().get("np", None) is None:
        warn(NUMPY_NOT_FOUND)
        return None

    cell = np.asarray(cell)

    volume = np.dot(cell[0], np.cross(cell[1], cell[2]))
    scale = []
    for i in range(3):
        vector = np.cross(cell[(i + 1) % 3], cell[(i + 2) % 3]) / volume
        scale.append(tuple(vector))
    return tuple(scale)


def fractional_coordinates(
    cell: Tuple[Vector3D, Vector3D, Vector3D], cartesian_positions: List[Vector3D]
) -> List[Vector3D]:
    """Returns fractional coordinates and wraps coordinates to be [0;1[

    NOTE: Based on `ase.atoms:Atoms.get_scaled_positions()`.
    """
    if globals().get("np", None) is None:
        warn(NUMPY_NOT_FOUND)
        return None

    cell = np.asarray(cell)
    cartesian_positions = np.asarray(cartesian_positions)

    fractional = np.linalg.solve(cell.T, cartesian_positions.T).T

    # Expecting a bulk 3D structure here, note, this may change in the future.
    # See `ase.atoms:Atoms.get_scaled_positions()` for ideas on how to handle lower dimensional structures.
    # Furthermore, according to ASE we need to modulo 1.0 twice.
    # This seems to be due to small floats % 1.0 becomes 1.0, hence twice makes it 0.0.
    for i in range(3):
        fractional[:, i] %= 1.0
        fractional[:, i] %= 1.0

    return [tuple(position) for position in fractional]


def cell_to_cellpar(cell, radians=False):
    """Returns the cell parameters [a, b, c, alpha, beta, gamma].

    Angles are in degrees unless radian=True is used.

    NOTE: Based on `ase.geometry.cell:cell_to_cellpar()`.
    """
    if globals().get("np", None) is None:
        warn(NUMPY_NOT_FOUND)
        return None

    cell = np.asarray(cell)

    lengths = [np.linalg.norm(vector) for vector in cell]
    angles = []
    for i in range(3):
        j = i - 1
        k = i - 2
        outer_product = lengths[j] * lengths[k]
        if outer_product > 1e-16:
            x_vector = np.dot(cell[j], cell[k]) / outer_product
            angle = 180.0 / np.pi * np.arccos(x_vector)
        else:
            angle = 90.0
        angles.append(angle)
    if radians:
        angles = [angle * np.pi / 180 for angle in angles]
    return np.array(lengths + angles)


def unit_vector(x):
    """Return a unit vector in the same direction as x."""
    if globals().get("np", None) is None:
        warn(NUMPY_NOT_FOUND)
        return None

    y = np.array(x, dtype="float")
    return y / np.linalg.norm(y)


def cellpar_to_cell(cellpar, ab_normal=(0, 0, 1), a_direction=None):
    """Return a 3x3 cell matrix from cellpar=[a,b,c,alpha,beta,gamma].

    Angles must be in degrees.

    The returned cell is orientated such that a and b
    are normal to `ab_normal` and a is parallel to the projection of
    `a_direction` in the a-b plane.

    Default `a_direction` is (1,0,0), unless this is parallel to
    `ab_normal`, in which case default `a_direction` is (0,0,1).

    The returned cell has the vectors va, vb and vc along the rows. The
    cell will be oriented such that va and vb are normal to `ab_normal`
    and va will be along the projection of `a_direction` onto the a-b
    plane.

    Example:

    >>> cell = cellpar_to_cell([1, 2, 4, 10, 20, 30], (0, 1, 1), (1, 2, 3))
    >>> np.round(cell, 3)
    array([[ 0.816, -0.408,  0.408],
           [ 1.992, -0.13 ,  0.13 ],
           [ 3.859, -0.745,  0.745]])

    NOTE: Direct copy of `ase.geometry.cell:cellpar_to_cell()`.
    """
    if globals().get("np", None) is None:
        warn(NUMPY_NOT_FOUND)
        return None

    if a_direction is None:
        if np.linalg.norm(np.cross(ab_normal, (1, 0, 0))) < 1e-5:
            a_direction = (0, 0, 1)
        else:
            a_direction = (1, 0, 0)

    # Define rotated X,Y,Z-system, with Z along ab_normal and X along
    # the projection of a_direction onto the normal plane of Z.
    a_direction_array = np.array(a_direction)
    Z = unit_vector(ab_normal)
    X = unit_vector(a_direction_array - np.dot(a_direction_array, Z) * Z)
    Y = np.cross(Z, X)

    # Express va, vb and vc in the X,Y,Z-system
    alpha, beta, gamma = 90.0, 90.0, 90.0
    if isinstance(cellpar, (int, float)):
        a = b = c = cellpar
    elif len(cellpar) == 1:
        a = b = c = cellpar[0]
    elif len(cellpar) == 3:
        a, b, c = cellpar
    else:
        a, b, c, alpha, beta, gamma = cellpar

    # Handle orthorhombic cells separately to avoid rounding errors
    eps = 2 * np.spacing(90.0, dtype=np.float64)  # around 1.4e-14
    # alpha
    if abs(abs(alpha) - 90) < eps:
        cos_alpha = 0.0
    else:
        cos_alpha = np.cos(alpha * np.pi / 180.0)
    # beta
    if abs(abs(beta) - 90) < eps:
        cos_beta = 0.0
    else:
        cos_beta = np.cos(beta * np.pi / 180.0)
    # gamma
    if abs(gamma - 90) < eps:
        cos_gamma = 0.0
        sin_gamma = 1.0
    elif abs(gamma + 90) < eps:
        cos_gamma = 0.0
        sin_gamma = -1.0
    else:
        cos_gamma = np.cos(gamma * np.pi / 180.0)
        sin_gamma = np.sin(gamma * np.pi / 180.0)

    # Build the cell vectors
    va = a * np.array([1, 0, 0])
    vb = b * np.array([cos_gamma, sin_gamma, 0])
    cx = cos_beta
    cy = (cos_alpha - cos_beta * cos_gamma) / sin_gamma
    cz_sqr = 1.0 - cx * cx - cy * cy
    assert cz_sqr >= 0
    cz = np.sqrt(cz_sqr)
    vc = c * np.array([cx, cy, cz])

    # Convert to the Cartesian x,y,z-system
    abc = np.vstack((va, vb, vc))
    T = np.vstack((X, Y, Z))
    cell = np.dot(abc, T)

    return cell


def _pad_iter_of_iters(
    iterable: Iterable[Iterable],
    padding: float = None,
    outer: Iterable = None,
    inner: Iterable = None,
) -> Tuple[Iterable[Iterable], bool]:
    """Turn any null/None values into a float in given iterable of iterables"""
    try:
        padding = float(padding)
    except (TypeError, ValueError):
        padding = float("nan")

    outer = outer if outer is not None else list
    inner = inner if outer is not None else tuple

    padded_iterable = any(
        value is None for inner_iterable in iterable for value in inner_iterable
    )

    if padded_iterable:
        padded_iterable_of_iterables = []
        for inner_iterable in iterable:
            new_inner_iterable = inner(
                value if value is not None else padding for value in inner_iterable
            )
            padded_iterable_of_iterables.append(new_inner_iterable)
        iterable = outer(padded_iterable_of_iterables)

    return iterable, padded_iterable


def pad_positions(
    positions: List[Vector3D], padding: float = None
) -> Tuple[List[Vector3D], bool]:
    """Turn any null/None values into a float in given list of positions"""
    return _pad_iter_of_iters(
        iterable=positions, padding=padding, outer=list, inner=tuple,
    )


def pad_cell(
    lattice_vectors: Tuple[Vector3D, Vector3D, Vector3D], padding: float = None
) -> Tuple[Tuple[Vector3D, Vector3D, Vector3D], bool]:
    """Turn any null/None values into a float in given tuple of lattice_vectors"""
    return _pad_iter_of_iters(
        iterable=lattice_vectors, padding=padding, outer=tuple, inner=tuple,
    )
