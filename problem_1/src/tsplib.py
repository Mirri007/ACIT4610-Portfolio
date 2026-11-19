# AI attribution: generated with Claude Code (Anthropic, Claude Opus 5.5). See docs/ai_declaration.md.
"""
Loading and validating TSPLIB instance files (assignment Problem 1, Part A).

What is a TSPLIB file?
----------------------
TSPLIB is a standard library of Travelling Salesman Problem benchmarks. A `.tsp` file is plain
text with two parts:

1. A *header* of "KEY : VALUE" lines, for example::

       NAME : eil51
       TYPE : TSP
       DIMENSION : 51
       EDGE_WEIGHT_TYPE : EUC_2D

2. A *data section* that starts with the line ``NODE_COORD_SECTION``. Each following line is
   ``<city id> <x coordinate> <y coordinate>``. The file ends with ``EOF``.

The assignment provides the files compressed (``.tsp.gz``). We keep the original compressed
files unchanged in the repository and decompress them in memory with Python's ``gzip`` module
when loading ("decompress it before loading").

Why validate?
-------------
The assignment requires us to check NAME, TYPE, DIMENSION, EDGE_WEIGHT_TYPE and
NODE_COORD_SECTION, and to require TYPE = TSP, EDGE_WEIGHT_TYPE = EUC_2D, exactly DIMENSION
coordinate rows and unique city identifiers. If a file were damaged or of a different kind,
every distance and every result built on it would be silently wrong, so we stop with a clear
error message instead.
"""

import gzip
from dataclasses import dataclass
from pathlib import Path

import numpy as np


# The header keys that the assignment says we must find and check.
REQUIRED_HEADER_KEYS = ("NAME", "TYPE", "DIMENSION", "EDGE_WEIGHT_TYPE")


class TSPLIBFormatError(ValueError):
    """Raised when a TSPLIB file is missing information or breaks an assignment rule."""


@dataclass
class TSPInstance:
    """
    One loaded and validated TSP instance.

    Attributes
    ----------
    name : str
        The NAME field from the file, e.g. "berlin52".
    dimension : int
        Number of cities (the DIMENSION field).
    coordinates : numpy.ndarray, shape (dimension, 2)
        Row k holds the (x, y) coordinates of city id k + 1.
        In other words, Python index 0 is TSPLIB city 1, index 1 is city 2, and so on.
        This "subtract 1" convention is used everywhere in the TSP code, because Python
        arrays start counting at 0 while TSPLIB city ids start at 1.
    comment : str
        The optional COMMENT field (only kept for information).
    """

    name: str
    dimension: int
    coordinates: np.ndarray
    comment: str = ""


def read_text_file(file_path):
    """
    Return the text content of a file, decompressing it first if it ends with ".gz".

    Why: the official TSPLIB downloads are gzip-compressed. Reading them through
    ``gzip.open`` decompresses in memory, so the original files never need to be modified.
    """
    file_path = Path(file_path)
    if file_path.suffix == ".gz":
        with gzip.open(file_path, mode="rt", encoding="ascii") as handle:
            return handle.read()
    return file_path.read_text(encoding="ascii")


def parse_tsplib_text(text):
    """
    Parse the text of a TSPLIB ``.tsp`` file into a header dictionary and coordinate rows.

    This function only *reads* the file structure. All assignment rules are checked
    afterwards in :func:`validate_and_build_instance`, which keeps "reading" and
    "checking" separate and easier to follow.

    Parameters
    ----------
    text : str
        Full content of the file.

    Returns
    -------
    header : dict[str, str]
        Header keys (upper case) mapped to their values as strings.
    coordinate_rows : list[tuple[int, float, float]]
        Every row found in NODE_COORD_SECTION as (city id, x, y).
    found_coordinate_section : bool
        True if the line NODE_COORD_SECTION was present.
    """
    header = {}
    coordinate_rows = []
    found_coordinate_section = False
    inside_coordinate_section = False

    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if line == "":
            continue  # blank lines carry no information (berlin52 ends with one)
        if line == "EOF":
            break  # official end-of-file marker

        if line == "NODE_COORD_SECTION":
            found_coordinate_section = True
            inside_coordinate_section = True
            continue

        if inside_coordinate_section:
            # A coordinate row looks like "12 37.0 52.0": city id, x, y.
            parts = line.split()
            if len(parts) != 3:
                raise TSPLIBFormatError(
                    f"Line {line_number}: expected 'id x y' in NODE_COORD_SECTION, got {line!r}"
                )
            try:
                city_id = int(parts[0])
                x_coordinate = float(parts[1])  # float() also accepts forms such as 1.2e+03
                y_coordinate = float(parts[2])
            except ValueError as error:
                raise TSPLIBFormatError(
                    f"Line {line_number}: could not read numbers from {line!r}"
                ) from error
            coordinate_rows.append((city_id, x_coordinate, y_coordinate))
        else:
            # Header lines use "KEY : VALUE". Files differ in spacing ("NAME: x" vs
            # "NAME : x"), so we split on the first colon and strip spaces from both sides.
            if ":" not in line:
                raise TSPLIBFormatError(f"Line {line_number}: expected 'KEY : VALUE', got {line!r}")
            key, value = line.split(":", 1)
            header[key.strip().upper()] = value.strip()

    return header, coordinate_rows, found_coordinate_section


def validate_and_build_instance(header, coordinate_rows, found_coordinate_section, source="file"):
    """
    Check every assignment rule and, if all pass, return a :class:`TSPInstance`.

    Checks performed (assignment Part A, "Data and Distance Calculation"):

    1. NAME, TYPE, DIMENSION and EDGE_WEIGHT_TYPE are all present.
    2. TYPE is exactly "TSP" (not e.g. "ATSP" or "TOUR").
    3. EDGE_WEIGHT_TYPE is exactly "EUC_2D" (our distance formula is only valid for that type).
    4. DIMENSION is a positive whole number.
    5. A NODE_COORD_SECTION exists.
    6. The number of coordinate rows equals DIMENSION.
    7. City ids are unique.
    8. City ids are exactly 1, 2, ..., DIMENSION. This is stricter than "unique", but our code
       stores city id k at array index k - 1 and fixes city 1 as the start of every tour,
       so every id in that range must exist.

    Raises
    ------
    TSPLIBFormatError
        With a message naming the rule that failed.
    """
    # Rule 1: required header fields are present.
    for key in REQUIRED_HEADER_KEYS:
        if key not in header:
            raise TSPLIBFormatError(f"{source}: missing required header field {key}")

    # Rule 2 and 3: correct problem type and distance type.
    if header["TYPE"] != "TSP":
        raise TSPLIBFormatError(f"{source}: TYPE must be TSP, found {header['TYPE']!r}")
    if header["EDGE_WEIGHT_TYPE"] != "EUC_2D":
        raise TSPLIBFormatError(
            f"{source}: EDGE_WEIGHT_TYPE must be EUC_2D, found {header['EDGE_WEIGHT_TYPE']!r}"
        )

    # Rule 4: DIMENSION is a positive integer.
    try:
        dimension = int(header["DIMENSION"])
    except ValueError as error:
        raise TSPLIBFormatError(f"{source}: DIMENSION is not an integer: {header['DIMENSION']!r}") from error
    if dimension < 1:
        raise TSPLIBFormatError(f"{source}: DIMENSION must be positive, found {dimension}")

    # Rule 5: the coordinate section exists.
    if not found_coordinate_section:
        raise TSPLIBFormatError(f"{source}: NODE_COORD_SECTION is missing")

    # Rule 6: one row per city.
    if len(coordinate_rows) != dimension:
        raise TSPLIBFormatError(
            f"{source}: DIMENSION is {dimension} but NODE_COORD_SECTION has {len(coordinate_rows)} rows"
        )

    # Rule 7: no city id appears twice.
    city_ids = [row[0] for row in coordinate_rows]
    if len(set(city_ids)) != len(city_ids):
        duplicates = sorted({city_id for city_id in city_ids if city_ids.count(city_id) > 1})
        raise TSPLIBFormatError(f"{source}: duplicate city ids {duplicates}")

    # Rule 8: ids are exactly 1..dimension (so none is missing and none is out of range).
    if set(city_ids) != set(range(1, dimension + 1)):
        missing = sorted(set(range(1, dimension + 1)) - set(city_ids))
        unexpected = sorted(set(city_ids) - set(range(1, dimension + 1)))
        raise TSPLIBFormatError(
            f"{source}: city ids must be 1..{dimension}; missing {missing}, unexpected {unexpected}"
        )

    # Store coordinates so that array row (id - 1) belongs to city id. The file normally lists
    # cities in order already, but placing each row by its id makes this independent of order.
    coordinates = np.zeros((dimension, 2), dtype=float)
    for city_id, x_coordinate, y_coordinate in coordinate_rows:
        coordinates[city_id - 1] = (x_coordinate, y_coordinate)

    return TSPInstance(
        name=header["NAME"],
        dimension=dimension,
        coordinates=coordinates,
        comment=header.get("COMMENT", ""),
    )


def load_tsplib_instance(file_path, expected_name=None, expected_dimension=None):
    """
    Load a TSPLIB ``.tsp`` or ``.tsp.gz`` file and validate it against the assignment rules.

    Parameters
    ----------
    file_path : str or Path
        Location of the file.
    expected_name, expected_dimension : optional
        If given, also check that the file is the instance we think it is
        (e.g. NAME "berlin52" with 52 cities, as listed in the assignment table).

    Returns
    -------
    TSPInstance
        The validated instance with coordinates indexed by (city id - 1).
    """
    text = read_text_file(file_path)
    header, coordinate_rows, found_section = parse_tsplib_text(text)
    instance = validate_and_build_instance(header, coordinate_rows, found_section, source=str(file_path))

    if expected_name is not None and instance.name != expected_name:
        raise TSPLIBFormatError(f"{file_path}: expected NAME {expected_name!r}, found {instance.name!r}")
    if expected_dimension is not None and instance.dimension != expected_dimension:
        raise TSPLIBFormatError(
            f"{file_path}: expected DIMENSION {expected_dimension}, found {instance.dimension}"
        )
    return instance
