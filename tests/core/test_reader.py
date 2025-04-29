"""Test file readers."""

from pathlib import Path

import pytest

import rascal2.core.readers as readers

DATA_PATH = Path(__file__, "../../data/").resolve()


@pytest.mark.parametrize(
    "filename, expected_size",
    (
        ["moto.dat", (400, 3)],
        ["orso_poly.dat", (408, 3)],
    ),
)
def test_read_csv(filename, expected_size):
    """Test the plaintext reader successfully reads in data."""
    data = readers.TextDataReader().read(DATA_PATH / filename)
    assert next(data).data.shape == expected_size


@pytest.mark.parametrize("filename, expected_size", (["f88904_06.asc", (93, 3)],))
def test_read_asc(filename, expected_size):
    """Test the .asc reader successfully reads in data."""
    data = readers.AscDataReader().read(DATA_PATH / filename)
    assert next(data).data.shape == expected_size


@pytest.mark.parametrize("filename, expected_size", (["INTER_61440_IvsQ_binned.nxs", (134, 3)],))
def test_read_nxs(filename, expected_size):
    """Test the .nxs reader successfully reads in data."""
    data = readers.NexusDataReader().read(DATA_PATH / filename)
    assert next(data).data.shape == expected_size


@pytest.mark.parametrize(
    "filename, expected_name, expected_size",
    (
        ["bare_substrate.ort", "D2O substrate", (53, 4)],
        ["prist5_10K_m_025.Rqz.ort", "prist4", (79, 4)],
    ),
)
def test_read_ort(filename, expected_name, expected_size):
    """Test the .ort reader successfully reads in data."""
    data = readers.OrtDataReader().read(DATA_PATH / filename)
    dataset = next(data)
    assert dataset.name == expected_name
    assert dataset.data.shape == expected_size
