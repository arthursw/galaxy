"""
Collection Mapping Data Structures

This module contains classes for representing dataset collections and
implementing Galaxy's collection matching logic for workflow execution.
"""

from pathlib import Path
from typing import Dict, List, Union


class CollectionElement:
    """Represents a single element in a dataset collection.

    Tracks the element identifier (for matching across workflow branches)
    and the actual file path.
    """

    def __init__(self, element_identifier: str, dataset_path: str):
        self.element_identifier = element_identifier
        self.dataset_path = dataset_path

    def __repr__(self):
        return f"CollectionElement(id='{self.element_identifier}', path='{self.dataset_path}')"


class DatasetCollection:
    """Represents a collection of datasets with a specific structure.

    Mimics Galaxy's dataset collection structure to enable workflow
    mapping over collections.
    """

    def __init__(self, collection_type: str, elements: List[CollectionElement]):
        self.collection_type = collection_type  # e.g., "list", "paired", "list:paired"
        self.elements = elements

    def __repr__(self):
        return f"DatasetCollection(type='{self.collection_type}', elements={len(self.elements)})"

    def get_element_identifiers(self) -> List[str]:
        """Return list of element identifiers in order."""
        return [e.element_identifier for e in self.elements]


def load_workflow_inputs(input_json_path: str) -> Dict[str, Union[str, DatasetCollection]]:
    """Load workflow inputs from JSON file.

    JSON format:
    {
      "inputs": {
        "0": {
          "collection_type": "list",
          "elements": [
            {"identifier": "image_1", "path": "/path/to/image_1.tif"},
            {"identifier": "image_2", "path": "/path/to/image_2.tif"}
          ]
        },
        "1": {
          "path": "/path/to/single_file.txt"
        }
      }
    }

    Args:
        input_json_path: Path to JSON file containing workflow inputs

    Returns:
        Dict mapping step IDs to either file paths (str) or DatasetCollections
    """
    import json

    with open(input_json_path) as f:
        data = json.load(f)

    parsed_inputs = {}
    for step_id, input_data in data.get("inputs", {}).items():
        if "collection_type" in input_data:
            # It's a collection
            elements = [
                CollectionElement(e["identifier"], e["path"])
                for e in input_data["elements"]
            ]
            parsed_inputs[step_id] = DatasetCollection(
                input_data["collection_type"],
                elements
            )
        else:
            # Single dataset
            parsed_inputs[step_id] = input_data["path"]

    return parsed_inputs


def match_collections(
    step_outputs: Dict[str, Dict[str, Union[str, DatasetCollection]]],
    input_connections: Dict[str, Union[dict, list]]
) -> List[Dict[str, str]]:
    """Match multiple input collections by element identifiers.

    This implements Galaxy's collection matching logic: when a tool receives
    multiple collection inputs, it must match elements by their identifiers
    across all collections. This ensures that when workflow branches rejoin,
    the correct datasets are paired together.

    Args:
        step_outputs: Dict of previous step outputs (step_id -> output_name -> data)
        input_connections: Dict of input connections for current step

    Returns:
        List of dicts mapping input names to file paths for each iteration.
        If no collections are found, returns a single empty dict for one execution.

    Example:
        If input_connections has:
          - 'label1' connected to collection [img1.c1, img2.c1, img3.c1]
          - 'label2' connected to collection [cell1, cell2, cell3]

        Returns:
          [
            {'label1': 'img1.c1', 'label2': 'cell1'},
            {'label1': 'img2.c1', 'label2': 'cell2'},
            {'label1': 'img3.c1', 'label2': 'cell3'}
          ]
    """
    collections_to_match = {}

    # Identify which inputs are collections
    for input_name, connection_info in input_connections.items():
        # Handle both single connection (dict) and multiple connections (list)
        if isinstance(connection_info, list):
            # For now, we'll handle the first connection
            # (multiple connections to same input is a more complex case)
            if not connection_info:
                continue
            connection_info = connection_info[0]

        source_step_id = str(connection_info.get('id'))
        source_output_name = connection_info.get('output_name', 'output')

        if source_step_id in step_outputs:
            source_data = step_outputs[source_step_id].get(source_output_name)
            if isinstance(source_data, DatasetCollection):
                collections_to_match[input_name] = source_data

    if not collections_to_match:
        # No collections to match, single execution with no collection params
        return [{}]

    # Verify all collections have same element identifiers
    all_identifiers = None
    collection_names = list(collections_to_match.keys())

    for input_name, collection in collections_to_match.items():
        coll_identifiers = collection.get_element_identifiers()
        if all_identifiers is None:
            all_identifiers = coll_identifiers
        elif coll_identifiers != all_identifiers:
            raise ValueError(
                f"Collection element identifiers don't match:\n"
                f"  {collection_names[0]}: {all_identifiers}\n"
                f"  {input_name}: {coll_identifiers}\n"
                f"All collections must have the same element identifiers for mapping."
            )

    # Create iteration slices - one per element identifier
    iteration_slices = []
    for i, identifier in enumerate(all_identifiers):
        slice_dict = {}
        for input_name, collection in collections_to_match.items():
            slice_dict[input_name] = collection.elements[i].dataset_path
        slice_dict['__element_identifier__'] = identifier
        iteration_slices.append(slice_dict)

    return iteration_slices
