/**
 * Store for managing the code-server panel state
 */

import { defineStore } from "pinia";
import { ref } from "vue";
import type { Tool } from "./toolStore";

export interface OpenToolResponse {
    id: string;
    tool_dir: string;
    config_file: string;
    files: string[];
    external_editor: boolean;
    status: string;
}

export const useCodeServerStore = defineStore("codeServerStore", () => {
    const showPanel = ref(false);
    const currentTool = ref<Tool | null>(null);
    const currentToolDir = ref<string>("");
    const currentConfigFile = ref<string>("");
    const panelWidth = ref(typeof window !== "undefined" ? window.innerWidth / 2 : 400); // Default width to half of screen

    function openPanel(tool: Tool, response?: OpenToolResponse) {
        currentTool.value = tool;
        currentToolDir.value = response?.tool_dir || "";
        currentConfigFile.value = response?.config_file || "";
        showPanel.value = true;
    }

    function closePanel() {
        showPanel.value = false;
        // Don't clear the tool immediately, let it stay in memory briefly
    }

    function setPanelWidth(width: number) {
        // Constrain width between 40% and 100% of window
        const minWidth = Math.max(window.innerWidth * 0.4, 300);
        const maxWidth = window.innerWidth;
        panelWidth.value = Math.min(Math.max(width, minWidth), maxWidth);
    }

    return {
        showPanel,
        currentTool,
        currentToolDir,
        currentConfigFile,
        panelWidth,
        openPanel,
        closePanel,
        setPanelWidth,
    };
});
