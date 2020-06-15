import math

import pytest

from .utils import get_min_ver

min_ver = get_min_ver("numpy")
numpy = pytest.importorskip(
    "numpy",
    minversion=min_ver,
    reason=f"numpy must be installed with minimum version {min_ver} for these tests to"
    " be able to run",
)

from optimade.adapters.structures.utils import (
    fractional_coordinates,
    pad_cell,
    pad_positions,
    scaled_cell,
)


# TODO: Add tests for cell_to_cellpar, unit_vector, cellpar_to_cell


def test_pad_positions(null_position_structure):
    """Make sure None values in cartesian_site_positions are converted to padding float value"""
    positions, padded_position = pad_positions(
        null_position_structure.attributes.cartesian_site_positions
    )

    assert not any(value is None for vector in positions for value in vector)
    assert padded_position

    positions, padded_position = pad_positions(positions)

    assert not any(value is None for vector in positions for value in vector)
    assert not padded_position


def test_pad_cell(null_lattice_vector_structure):
    """Make sure None values in lattice_vectors are converted to padding float value"""
    lattice_vectors, padded_cell = pad_cell(
        null_lattice_vector_structure.attributes.lattice_vectors
    )

    assert not any(value is None for vector in lattice_vectors for value in vector)
    assert padded_cell

    lattice_vectors, padded_cell = pad_cell(lattice_vectors)

    assert not any(value is None for vector in lattice_vectors for value in vector)
    assert not padded_cell


def test__pad_iter_of_iters():
    """Test _pad_iter_of_iters"""
    iterable = [(0.0,) * 3, (0.0,) * 3, (None,) * 3]

    padded_iterable, padded_iterable_bool = pad_cell(iterable)

    assert padded_iterable_bool
    assert all(math.isnan(_) for _ in padded_iterable[-1])
    for i in range(2):
        assert padded_iterable[i] == (0.0,) * 3

    for valid_padding_value in (3.0, 3, "3", "3.0"):
        padded_iterable, padded_iterable_bool = pad_cell(iterable, valid_padding_value)

        assert padded_iterable_bool
        assert padded_iterable[-1] == (float(valid_padding_value),) * 3
        for i in range(2):
            assert padded_iterable[i] == (0.0,) * 3

    # Since nan != nan, the above for-loop cannot be used for nan
    valid_padding_value = "nan"
    padded_iterable, padded_iterable_bool = pad_cell(iterable, valid_padding_value)

    assert padded_iterable_bool
    assert all(math.isnan(_) for _ in padded_iterable[-1])
    assert all(math.isnan(_) for _ in (float(valid_padding_value),) * 3)
    for i in range(2):
        assert padded_iterable[i] == (0.0,) * 3

    invalid_padding_value = "x"
    padded_iterable, padded_iterable_bool = pad_cell(iterable, invalid_padding_value)

    assert padded_iterable_bool
    assert all(math.isnan(_) for _ in padded_iterable[-1])
    for i in range(2):
        assert padded_iterable[i] == (0.0,) * 3


def test_scaled_cell_and_fractional_coordinates(structures):
    """Make sure these two different calculations arrive at the same result"""
    for structure in structures:
        scale = scaled_cell(structure.lattice_vectors)
        scale = numpy.asarray(scale)
        cartesian_positions = numpy.asarray(structure.cartesian_site_positions)
        scaled_fractional_positions = (scale.T @ cartesian_positions.T).T
        for i in range(3):
            scaled_fractional_positions[:, i] %= 1.0
            scaled_fractional_positions[:, i] %= 1.0
        scaled_fractional_positions = [
            tuple(position) for position in scaled_fractional_positions
        ]

        calculated_fractional_positions = fractional_coordinates(
            cell=structure.lattice_vectors,
            cartesian_positions=structure.cartesian_site_positions,
        )

        for scaled_position, calculated_position in zip(
            scaled_fractional_positions, calculated_fractional_positions
        ):
            assert scaled_position == pytest.approx(calculated_position)


def test_scaled_cell_consistency(structure):
    """Test scaled_cell's PDB-designated validation: inverse of det(SCALE) = Volume of cell"""
    # Manual calculation of volume = |a_1 . (a_2 x a_3)|
    a_1 = structure.lattice_vectors[0]
    a_2 = structure.lattice_vectors[1]
    a_3 = structure.lattice_vectors[2]
    a_mid_0 = a_2[1] * a_3[2] - a_2[2] * a_3[1]
    a_mid_1 = a_2[2] * a_3[0] - a_2[0] * a_3[2]
    a_mid_2 = a_2[0] * a_3[1] - a_2[1] * a_3[0]
    volume_from_cellpar = abs(a_1[0] * a_mid_0 + a_1[1] * a_mid_1 + a_1[2] * a_mid_2)

    scale = scaled_cell(structure.lattice_vectors)
    volume_from_scale = 1 / numpy.linalg.det(scale)

    assert volume_from_scale == pytest.approx(volume_from_cellpar)
