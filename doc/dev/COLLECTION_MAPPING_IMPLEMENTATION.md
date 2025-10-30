# Galaxy Collection Mapping: How It Works & Implementation Plan

## Part 1: How Galaxy Does Collection Mapping

### Core Concepts

**1. Dataset Collections Structure**

Galaxy uses a tree-based structure to represent collections:
- **Leaf**: Represents a single dataset
- **Tree**: Represents a collection with nested elements, each identified by an `element_identifier`
- Collections maintain their hierarchical structure: `list`, `paired`, `list:paired`, etc.

**2. Element Identifiers**

Element identifiers are the key to tracking data through workflow branches:
- Each element in a collection has a unique `element_identifier` (e.g., "sample1", "sample2")
- These identifiers are preserved throughout the workflow execution
- When branches rejoin, Galaxy matches elements by their identifiers

**3. Collection Matching Process**

Galaxy uses three main classes for collection mapping:

**a. `CollectionsToMatch`** (`lib/galaxy/model/dataset_collections/matching.py`)
- Accumulates all input collections that need to be matched for a workflow step
- Stores each collection with its input name and subcollection type
- Distinguishes between "linked" (must match structure) and "unlinked" collections

**b. `MatchingCollections`**
- Result of matching collections together
- Contains:
  - `linked_structure`: The common structure all linked collections must match
  - `collections`: Dict mapping input names to collection instances
  - `subcollection_types`: Subcollection types for each input
  - `when_values`: Conditional execution tracking

**c. Structure Classes** (`lib/galaxy/model/dataset_collections/structure.py`)
- `Tree`: Represents known collection structure with children
- `UninitializedTree`: Represents collections with unknown structure at planning time
- `Leaf`: Terminal node (single dataset)

**4. The Mapping Algorithm**

When a workflow step receives collection inputs, Galaxy:

1. **Collects inputs to match** (`WorkflowModule.compute_collection_info`):
   - Iterates through all step inputs
   - For each input that is a collection with `allow_implicit_mapping=True`
   - Adds to `CollectionsToMatch` with appropriate subcollection type

2. **Matches collections** (`DatasetCollectionManager.match_collections`):
   - Verifies all collections have compatible structures
   - Creates a `MatchingCollections` object with the unified structure
   - Validates that element counts and nesting levels match

3. **Slices collections** (`MatchingCollections.slice_collections`):
   - Calls `Tree.walk_collections()` which recursively walks the structure
   - For each element identifier, yields a dict: `{input_name: element}`
   - This dict maps each input parameter to the corresponding collection element

4. **Executes per element**:
   - For each slice from `slice_collections()`, the workflow step executes once
   - Element identifiers ensure proper pairing across branches

### Example: MultiFish Workflow

```
Input collection: [image_1, image_2, image_3]
                     |
                     v
              Split Channels (step 1)
                     |
        +------------+------------+
        |            |            |
       c1           c2           c3
        |            |            |
   [img_1.c1,   [img_1.c2,   [img_1.c3,
    img_2.c1,    img_2.c2,    img_2.c3,
    img_3.c1]    img_3.c2]    img_3.c3]
        |            |            |
      Atlas        Atlas       Cellpose
        |            |            |
  [atlas_1.c1,  [atlas_1.c2, [cell_1,
   atlas_2.c1,   atlas_2.c2,  cell_2,
   atlas_3.c1]   atlas_3.c2]  cell_3]
        |            |            |
        +------------+            |
                 |                |
           Label Overlaps (step 7)
                 |
        Matches: atlas_1.c1 with cell_1
                 atlas_2.c1 with cell_2
                 atlas_3.c1 with cell_3
```

**Key Points:**
- Each branch maintains element identifiers (image_1, image_2, image_3)
- When branches converge at "Label Overlaps", Galaxy matches by identifier
- The tool receives `label1=atlas_1.c1` paired with `label2=cell_1` automatically

## Part 2: Implementation

### JSON Input Format

```json
{
  "inputs": {
    "0": {
      "collection_type": "list",
      "elements": [
        {"identifier": "image_1", "path": "/path/to/image_1.tif"},
        {"identifier": "image_2", "path": "/path/to/image_2.tif"},
        {"identifier": "image_3", "path": "/path/to/image_3.tif"}
      ]
    }
  }
}
```

### Key Implementation Details

1. **CollectionElement**: Tracks element identifier and file path
2. **DatasetCollection**: Contains collection type and list of elements
3. **match_collections**: Matches collections by element identifiers across branches
4. **Element identifier preservation**: Outputs inherit identifiers from inputs

### Usage

```bash
python execute_workflow.py workflow.ga tool_conf.xml galaxy_root inputs.json
