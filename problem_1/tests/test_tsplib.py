# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Tests for TSPLIB loading and validation (assignment Part A, "Data and Distance Calculation").

Two groups of tests:
  1. The six real assignment files load correctly.
  2. Deliberately broken small files are rejected with a clear error, one test per rule.
"""

import numpy as np
import pytest

from src.tsp_instances import TSP_INSTANCES, instance_file_path
from src.tsplib import TSPLIBFormatError, load_tsplib_instance, parse_tsplib_text, validate_and_build_instance

# A tiny valid file used as the starting point for the "broken file" tests.
VALID_TEXT = """NAME : tiny4
TYPE : TSP
DIMENSION : 4
EDGE_WEIGHT_TYPE : EUC_2D
NODE_COORD_SECTION
1 0 0
2 3 0
3 3 4
4 0 4
EOF
"""


def build_from_text(text):
    """Parse + validate a TSPLIB text, the same two steps load_tsplib_instance uses."""
    header, rows, found_section = parse_tsplib_text(text)
    return validate_and_build_instance(header, rows, found_section, source="test")


# ---------------------------------------------------------------- real assignment files

@pytest.mark.parametrize("name", list(TSP_INSTANCES))
def test_all_six_assignment_instances_load(name):
    expected_cities, _optimum = TSP_INSTANCES[name]
    instance = load_tsplib_instance(instance_file_path(name), expected_name=name,
                                    expected_dimension=expected_cities)
    assert instance.name == name
    assert instance.dimension == expected_cities
    assert instance.coordinates.shape == (expected_cities, 2)


def test_berlin52_first_and_last_coordinates_match_the_file():
    # Values copied by hand from berlin52.tsp: "1 565.0 575.0" and "52 1740.0 245.0".
    instance = load_tsplib_instance(instance_file_path("berlin52"))
    assert tuple(instance.coordinates[0]) == (565.0, 575.0)
    assert tuple(instance.coordinates[51]) == (1740.0, 245.0)


def test_ch150_decimal_coordinates_are_read_exactly():
    # From ch150.tsp: "1 37.4393516691 541.2090699418"
    instance = load_tsplib_instance(instance_file_path("ch150"))
    assert instance.coordinates[0, 0] == pytest.approx(37.4393516691)
    assert instance.coordinates[0, 1] == pytest.approx(541.2090699418)


def test_expected_name_mismatch_is_rejected():
    with pytest.raises(TSPLIBFormatError, match="expected NAME"):
        load_tsplib_instance(instance_file_path("eil51"), expected_name="berlin52")


# ---------------------------------------------------------------- valid variations

def test_valid_tiny_file_loads():
    instance = build_from_text(VALID_TEXT)
    assert instance.dimension == 4
    assert np.array_equal(instance.coordinates, [[0, 0], [3, 0], [3, 4], [0, 4]])


def test_header_spacing_variants_are_accepted():
    # Some TSPLIB files write "NAME: x", others "NAME : x".
    text = VALID_TEXT.replace("NAME : tiny4", "NAME: tiny4").replace("TYPE : TSP", "TYPE:TSP")
    assert build_from_text(text).name == "tiny4"


def test_rows_in_any_order_are_stored_by_city_id():
    text = VALID_TEXT.replace("1 0 0\n2 3 0\n", "2 3 0\n1 0 0\n")
    instance = build_from_text(text)
    assert tuple(instance.coordinates[0]) == (0, 0)   # city 1
    assert tuple(instance.coordinates[1]) == (3, 0)   # city 2


# ---------------------------------------------------------------- one test per broken rule

@pytest.mark.parametrize("missing_key", ["NAME", "TYPE", "DIMENSION", "EDGE_WEIGHT_TYPE"])
def test_missing_required_header_field_is_rejected(missing_key):
    lines = [line for line in VALID_TEXT.splitlines() if not line.startswith(missing_key + " ")]
    with pytest.raises(TSPLIBFormatError, match=f"missing required header field {missing_key}"):
        build_from_text("\n".join(lines))


def test_wrong_type_is_rejected():
    with pytest.raises(TSPLIBFormatError, match="TYPE must be TSP"):
        build_from_text(VALID_TEXT.replace("TYPE : TSP", "TYPE : ATSP"))


def test_wrong_edge_weight_type_is_rejected():
    with pytest.raises(TSPLIBFormatError, match="EDGE_WEIGHT_TYPE must be EUC_2D"):
        build_from_text(VALID_TEXT.replace("EUC_2D", "GEO"))


def test_non_integer_dimension_is_rejected():
    with pytest.raises(TSPLIBFormatError, match="DIMENSION is not an integer"):
        build_from_text(VALID_TEXT.replace("DIMENSION : 4", "DIMENSION : four"))


def test_missing_coordinate_section_is_rejected():
    text = VALID_TEXT.split("NODE_COORD_SECTION")[0]  # header only
    with pytest.raises(TSPLIBFormatError, match="NODE_COORD_SECTION is missing"):
        build_from_text(text)


def test_too_few_rows_is_rejected():
    with pytest.raises(TSPLIBFormatError, match="has 3 rows"):
        build_from_text(VALID_TEXT.replace("4 0 4\n", ""))


def test_too_many_rows_is_rejected():
    with pytest.raises(TSPLIBFormatError, match="has 5 rows"):
        build_from_text(VALID_TEXT.replace("4 0 4\n", "4 0 4\n5 1 1\n"))


def test_duplicate_city_id_is_rejected():
    with pytest.raises(TSPLIBFormatError, match="duplicate city ids \\[3\\]"):
        build_from_text(VALID_TEXT.replace("4 0 4", "3 0 4"))


def test_missing_city_id_is_rejected():
    # Ids 1, 2, 3, 5: unique, right count, but city 4 is missing.
    with pytest.raises(TSPLIBFormatError, match="missing \\[4\\]"):
        build_from_text(VALID_TEXT.replace("4 0 4", "5 0 4"))


def test_malformed_coordinate_row_is_rejected():
    with pytest.raises(TSPLIBFormatError, match="expected 'id x y'"):
        build_from_text(VALID_TEXT.replace("3 3 4", "3 3"))


def test_non_numeric_coordinate_is_rejected():
    with pytest.raises(TSPLIBFormatError, match="could not read numbers"):
        build_from_text(VALID_TEXT.replace("3 3 4", "3 three 4"))
