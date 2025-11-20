<template>
    <div class="code-server-panel">
        <div class="code-server-header">
            <h2 class="code-server-title">VS Code - {{ fileName }}</h2>
            <button class="code-server-close-btn" title="Close editor" @click="onClose">
                ×
            </button>
        </div>
        <div class="code-server-container">
            <iframe
                src="http://localhost:32344"
                class="code-server-iframe"
                title="VS Code Web Editor"
                frameborder="0"
                allow="clipboard-read; clipboard-write" />
        </div>
    </div>
</template>

<script setup lang="ts">
// eslint-disable-next-line import/order
import { computed, watch } from "vue";
// eslint-disable-next-line import/order
import type { Tool } from "@/stores/toolStore";

const EXTENSION_API_URL = "http://127.0.0.1:60351/open";

interface Props {
    tool?: Tool | null;
}

const props = withDefaults(defineProps<Props>(), {
    tool: null,
});

const emit = defineEmits<{
    (e: "close"): void;
}>();

const filePath = computed(() => props.tool?.config_file || "");

const fileName = computed(() => {
    if (!filePath.value) {
        return "No file";
    }
    return filePath.value.split("/").pop() || filePath.value;
});

/**
 * Call the VS Code extension API to open a file
 * This avoids reloading the iframe URL which would reset the editor
 */
async function openFileInVsCode(path: string) {
    try {
        const params = new URLSearchParams({
            path: path,
            type: "file",
            new_window: "false",
        });

        const response = await fetch(`${EXTENSION_API_URL}?${params}`, {
            method: "GET",
        });

        if (!response.ok) {
            console.warn(`Failed to open file in VS Code: ${response.statusText}`);
        }
    } catch (error) {
        console.error("Error calling VS Code extension API:", error);
    }
}

// Watch for changes to the tool and open the file in VS Code
watch(
    () => props.tool?.config_file,
    (newFilePath) => {
        if (newFilePath) {
            void openFileInVsCode(newFilePath);
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
