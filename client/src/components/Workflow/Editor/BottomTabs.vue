<script setup lang="ts">
import { storeToRefs } from "pinia";
import { computed } from "vue";

import { useWorkflowStores } from "@/composables/workflowStores";

const { stateStore } = useWorkflowStores();
const { activeTab } = storeToRefs(stateStore);

interface Tab {
    id: "dataset" | "run";
    label: string;
    icon: string;
}

const tabs: Tab[] = [
    { id: "dataset", label: "Step Datasets", icon: "fa-table" },
    { id: "run", label: "Run Workflow", icon: "fa-play" },
];

function toggleTab(tabId: "dataset" | "run") {
    if (activeTab.value === tabId) {
        // Click on active tab minimizes it
        activeTab.value = "none";
    } else {
        // Click on inactive tab switches to it
        activeTab.value = tabId;
    }
}

const isMinimized = computed(() => activeTab.value === "none");
</script>

<template>
    <div class="bottom-tabs-bar" :class="{ minimized: isMinimized }">
        <div class="tabs-container">
            <button
                v-for="tab in tabs"
                :key="tab.id"
                class="tab-button"
                :class="{ active: activeTab === tab.id }"
                :title="tab.label"
                @click="toggleTab(tab.id)">
                <i :class="['fas', tab.icon, 'mr-2']"></i>
                {{ tab.label }}
            </button>
        </div>
    </div>
</template>

<style scoped lang="scss">
.bottom-tabs-bar {
    position: relative;
    background: #f5f5f5;
    border-top: 1px solid #bdc6d0;
    height: auto;
    display: flex;
    flex-direction: column;
    z-index: 10;

    .tabs-container {
        display: flex;
        gap: 0;
        flex-wrap: nowrap;
    }

    .tab-button {
        flex: 0 1 auto;
        padding: 8px 16px;
        background: transparent;
        border: none;
        border-bottom: 3px solid transparent;
        cursor: pointer;
        font-size: 13px;
        color: #555;
        transition: all 0.2s ease;
        white-space: nowrap;
        display: flex;
        align-items: center;

        &:hover {
            background: #e8e8e8;
            color: #333;
        }

        &.active {
            background: white;
            border-bottom-color: #0066cc;
            color: #0066cc;
            font-weight: 500;
        }
    }
}
</style>
