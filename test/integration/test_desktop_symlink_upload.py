"""
Integration tests for desktop file upload via symlink (create_symlink endpoint)
Tests the complete workflow: symlink creation, state management, file access, and metadata
"""

import os
import tempfile

from galaxy_test.base.populators import DatasetPopulator
from galaxy_test.driver import integration_util


class TestDesktopSymlinkUpload(integration_util.IntegrationTestCase):
    """Test desktop mode symlink dataset creation"""

    dataset_populator: DatasetPopulator
    framework_tool_and_types = True

    def setUp(self):
        super().setUp()
        self.dataset_populator = DatasetPopulator(self.galaxy_interactor)
        self.history_id = self.dataset_populator.new_history()

        # Create a temporary test file to upload
        self.test_file_path = self._create_test_file()

    def tearDown(self):
        super().tearDown()
        # Clean up test file
        if os.path.exists(self.test_file_path):
            os.remove(self.test_file_path)

    @classmethod
    def handle_galaxy_config_kwds(cls, config):
        super().handle_galaxy_config_kwds(config)
        # Enable symlink datasets for desktop mode
        config["allow_local_file_symlinks"] = True

    def test_create_symlink_dataset_basic(self):
        """Test that create_symlink endpoint creates a dataset with correct metadata"""
        dataset_info = self._create_symlink_dataset()

        # Verify dataset was created
        assert dataset_info["id"] is not None
        assert dataset_info["extension"] == "png"
        assert dataset_info["state"] == "ok"
        assert dataset_info["name"] == "test_image.png"

    def test_create_symlink_dataset_preserves_extension(self):
        """Test that file extension is detected from source file"""
        dataset_info = self._create_symlink_dataset()

        # Extension should be 'png', not 'data'
        assert dataset_info["extension"] == "png"

    def test_create_symlink_dataset_sets_correct_state(self):
        """Test that dataset state is set to OK after creation"""
        dataset_info = self._create_symlink_dataset()

        # Check state in API response
        assert dataset_info["state"] == "ok"

        # Check state in database via detailed GET
        detailed = self._get(f"datasets/{dataset_info['id']}").json()
        assert detailed["state"] == "ok"

    def test_create_symlink_dataset_sets_file_size(self):
        """Test that dataset file size is calculated correctly"""
        dataset_info = self._create_symlink_dataset()

        # File size should be set and match actual file
        expected_size = os.path.getsize(self.test_file_path)
        assert dataset_info["file_size"] > 0, f"File size is 0, expected {expected_size}"
        assert dataset_info["file_size"] == expected_size, f"File size {dataset_info['file_size']} != {expected_size}"

    def test_create_symlink_dataset_appears_in_history(self):
        """Test that symlink dataset appears in history contents"""
        dataset_info = self._create_symlink_dataset()

        # Get history contents
        contents = self._get(f"histories/{self.history_id}/contents").json()

        # Find our dataset
        dataset_id = dataset_info["id"]
        found = any(item["id"] == dataset_id for item in contents)
        assert found, f"Dataset {dataset_id} not found in history contents"

    def test_create_symlink_dataset_rejects_nonexistent_file(self):
        """Test that create_symlink rejects files that don't exist"""
        response = self._post(
            "datasets/create_symlink",
            data={
                "file_path": "/nonexistent/path/file.png",
                "history_id": self.history_id,
                "extension": "png",
                "dbkey": "?",
            },
            json=True,
        )

        # Should fail with 400 or 404
        assert response.status_code in [400, 404, 422], f"Expected error status, got {response.status_code}"

    def test_multiple_symlink_datasets(self):
        """Test creating multiple symlink datasets in same history"""
        dataset1 = self._create_symlink_dataset()
        dataset2 = self._create_symlink_dataset()

        # Both should have different IDs
        assert dataset1["id"] != dataset2["id"]

        # Both should exist in history
        contents = self._get(f"histories/{self.history_id}/contents").json()
        ids = [item["id"] for item in contents]

        assert dataset1["id"] in ids
        assert dataset2["id"] in ids

    def test_symlink_dataset_metadata(self):
        """Test that dataset metadata is correct"""
        dataset_info = self._create_symlink_dataset()

        # Get detailed dataset info
        detailed = self._get(f"datasets/{dataset_info['id']}").json()

        # Should have name from file
        assert "test_image" in detailed["name"]

        # Should have correct extension
        assert detailed["extension"] == "png"

        # Should have HID (history item ID)
        assert detailed["hid"] is not None
        assert detailed["hid"] > 0

    def test_symlink_dataset_preview(self):
        """Test that symlink dataset can be previewed/displayed"""
        dataset_info = self._create_symlink_dataset()

        # Try to preview/display the dataset
        response = self._get(f"datasets/{dataset_info['id']}/display")

        # Should return 200 and actual file content
        assert response.status_code == 200, f"Preview failed with status {response.status_code}"

        # Verify we got actual PNG data back
        content = response.content
        assert len(content) > 0, "Preview returned empty content"
        assert content.startswith(b"\x89PNG"), "Preview didn't return PNG data"

    # Helper methods

    def _create_test_file(self):
        """Create a small test PNG file"""
        # Create a minimal PNG file (1x1 transparent pixel)
        png_data = (
            b"\x89PNG\r\n\x1a\n"
            b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
            b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01"
            b"\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82"
        )

        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, "test_image.png")

        with open(file_path, "wb") as f:
            f.write(png_data)

        return file_path

    def _create_symlink_dataset(self):
        """Create a dataset via the create_symlink endpoint"""
        response = self._post(
            "datasets/create_symlink",
            data={
                "file_path": self.test_file_path,
                "history_id": self.history_id,
                "extension": "auto",
                "dbkey": "?",
            },
            json=True,
        )

        self._assert_status_code_is_ok(response)
        return response.json()
