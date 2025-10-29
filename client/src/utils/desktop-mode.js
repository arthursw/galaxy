/**
 * Desktop mode utilities for Galaxy Desktop
 * Provides detection of desktop mode and file selection via pywebview
 */

/**
 * Check if running in desktop mode (pywebview)
 * @returns {boolean} True if running in desktop mode
 */
export function isDesktopMode() {
    return typeof window.pywebview !== "undefined";
}

/**
 * Select files using native file picker (desktop mode only)
 * @param {boolean} multiple - Allow multiple file selection
 * @returns {Promise<Array<Object>>} Array of file descriptors with path, name, size
 */
export async function selectDesktopFiles(multiple = true) {
    if (!isDesktopMode()) {
        throw new Error("Not in desktop mode");
    }

    try {
        const filePaths = await window.pywebview.api.select_files(multiple);

        if (!filePaths || filePaths.length === 0) {
            return [];
        }

        // Convert file paths to file descriptors
        return filePaths.map((path) => ({
            path: path,
            name: path.split("/").pop(), // Get filename from path
            size: null, // Size will be determined by server
            mode: "desktop",
        }));
    } catch (error) {
        console.error("Error selecting files in desktop mode:", error);
        throw error;
    }
}

/**
 * Create a dataset from a local file path via symlink (desktop mode only)
 * @param {string} filePath - Absolute path to the file
 * @param {string} historyId - History ID to add the dataset to
 * @param {Object} options - Additional options for the dataset
 * @returns {Promise<Object>} Created dataset information
 */
export async function createSymlinkDataset(filePath, historyId, options = {}) {
    if (!isDesktopMode()) {
        throw new Error("Symlink datasets only available in desktop mode");
    }

    const payload = {
        file_path: filePath,
        history_id: historyId,
        extension: options.extension || "auto",
        dbkey: options.dbkey || "?",
        name: options.name || null,
        space_to_tab: options.spaceToTab || false,
        to_posix_lines: options.toPosixLines || false,
    };

    try {
        const response = await fetch(`${window.location.origin}/api/datasets/create_symlink`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(payload),
        });

        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`Failed to create symlink dataset: ${response.statusText} - ${errorText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Error creating symlink dataset:", error);
        throw error;
    }
}

/**
 * Submit multiple files for symlink creation (desktop mode batch operation)
 * @param {Array<Object>} files - Array of file descriptors from selectDesktopFiles
 * @param {string} historyId - History ID
 * @param {Object} commonOptions - Common options for all files
 * @returns {Promise<Array<Object>>} Array of created datasets
 */
export async function submitDesktopFiles(files, historyId, commonOptions = {}) {
    if (!isDesktopMode()) {
        throw new Error("Desktop file submission only available in desktop mode");
    }

    const results = [];
    const errors = [];

    for (const file of files) {
        try {
            const options = {
                ...commonOptions,
                name: file.name,
            };
            const result = await createSymlinkDataset(file.path, historyId, options);
            results.push(result);
        } catch (error) {
            errors.push({
                file: file.name,
                error: error.message,
            });
        }
    }

    if (errors.length > 0) {
        console.warn("Some files failed to upload:", errors);
    }

    return {
        success: results,
        errors: errors,
    };
}
