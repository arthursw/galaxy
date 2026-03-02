/**
 * Store for managing the code-server panel state
 */

import { defineStore } from "pinia";
import { ref } from "vue";
import type { Tool } from "./toolStore";

export const useCodeServerStore = defineStore("codeServerStore", () => {
    const showPanel = ref(true);
    const currentTool = ref<Tool | null>(null);
    const panelWidth = ref(typeof window !== "undefined" ? window.innerWidth / 2 : 400); // Default width to half of screen

    function openPanel(tool: Tool) {
        currentTool.value = tool;
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
        panelWidth,
        openPanel,
        closePanel,
        setPanelWidth,
    };
});
