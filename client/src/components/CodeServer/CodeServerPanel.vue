<template>
    <div class="code-server-panel">
        <div class="code-server-header">
            <h2 class="code-server-title">VS Code: - {{ folderName }}</h2>
            <button class="code-server-close-btn" title="Close editor" @click="onClose">
                ×
            </button>
        </div>
        <div class="code-server-container">
            <iframe
                src="http://localhost:32344"
                class="code-server-iframe"
                title="VS Code: Web Editor"
                frameborder="0"
                allow="clipboard-read; clipboard-write" />
        </div>
    </div>
</template>

<script setup lang="ts">
// eslint-disable-next-line import/order
import { computed, watch } from "vue";

const EXTENSION_API_URL = "http://127.0.0.1:60351/open";

interface Props {
    toolDir?: string;
    configFile?: string;
}

const props = withDefaults(defineProps<Props>(), {
    toolDir: "",
    configFile: "",
});

const emit = defineEmits<{
    (e: "close"): void;
}>();

const folderName = computed(() => {
    if (!props.toolDir) {
        return "No folder";
    }
    return props.toolDir.split("/").pop() || props.toolDir;
});

/**
 * Call the VS Code: extension API to open a folder as workspace
 */
async function openFolderInVsCode(folderPath: string) {
    try {
        const params = new URLSearchParams({
            path: folderPath,
            type: "folder",
            new_window: "false",
        });

        const response = await fetch(`${EXTENSION_API_URL}?${params}`, {
            method: "GET",
        });

        if (!response.ok) {
            console.warn(`Failed to open folder in VS Code:: ${response.statusText}`);
        }
    } catch (error) {
        console.error("Error calling VS Code: extension API:", error);
    }
}

/**
 * Call the VS Code: extension API to open a file
 */
async function openFileInVsCode(filePath: string) {
    try {
        const params = new URLSearchParams({
            path: filePath,
            type: "file",
            new_window: "false",
        });

        const response = await fetch(`${EXTENSION_API_URL}?${params}`, {
            method: "GET",
        });

        if (!response.ok) {
            console.warn(`Failed to open file in VS Code:: ${response.statusText}`);
        }
    } catch (error) {
        console.error("Error calling VS Code: extension API:", error);
    }
}

// Watch for changes to the tool folder and open it in VS Code:
watch(
    () => props.toolDir,
    async (newToolDir) => {
        if (newToolDir) {
            // First open the folder as workspace
            await openFolderInVsCode(newToolDir);
            // Then open the config file if available
            if (props.configFile) {
                await openFileInVsCode(props.configFile);
            }
        }
    }
);

function onClose() {
    emit("close");
}
</script>

<style scoped>
.code-server-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: #1e1e1e;
    color: #d4d4d4;
}

.code-server-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 12px;
    border-bottom: 1px solid #3e3e42;
    background-color: #252526;
    flex-shrink: 0;
}

.code-server-title {
    margin: 0;
    font-size: 13px;
    font-weight: 600;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    flex: 1;
}

.code-server-close-btn {
    background: none;
    border: none;
    color: #d4d4d4;
    cursor: pointer;
    font-size: 20px;
    padding: 0 4px;
    margin-left: 8px;
    flex-shrink: 0;
    transition: color 0.2s;
}

.code-server-close-btn:hover {
    color: #ffffff;
}

.code-server-container {
    flex: 1;
    overflow: hidden;
    position: relative;
}

.code-server-iframe {
    width: 100%;
    height: 100%;
    border: none;
}
</style>
