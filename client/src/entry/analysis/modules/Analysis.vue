<script setup lang="ts">
/* eslint-disable import/order */
import { storeToRefs } from "pinia";
import { onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router/composables";

import ActivityBar from "@/components/ActivityBar/ActivityBar.vue";
import CodeServerPanel from "@/components/CodeServer/CodeServerPanel.vue";
import DragAndDropModal from "@/components/Upload/DragAndDropModal.vue";
import FlexPanel from "@/components/Panels/FlexPanel.vue";
import HistoryIndex from "@/components/History/Index.vue";
import { usePanels } from "@/composables/usePanels";
import { useCodeServerStore } from "@/stores/codeServerStore";
import { useUserStore } from "@/stores/userStore";

import CenterFrame from "./CenterFrame.vue";
/* eslint-enable import/order */

const router = useRouter();
const showCenter = ref(false);
const { showPanels } = usePanels();

const { historyPanelWidth } = storeToRefs(useUserStore());
const { showPanel, currentTool, panelWidth } = storeToRefs(useCodeServerStore());
const codeServerStore = useCodeServerStore();

const isDraggingCodeServerSeparator = ref(false);
const startX = ref(0);
const startWidth = ref(0);

// methods
function hideCenter() {
    showCenter.value = false;
}

function onLoad() {
    showCenter.value = true;
}

function startCodeServerResize(event: MouseEvent) {
    isDraggingCodeServerSeparator.value = true;
    startX.value = event.clientX;
    startWidth.value = panelWidth.value;
}

function handleCodeServerResize(event: MouseEvent) {
    if (!isDraggingCodeServerSeparator.value) {
        return;
    }

    const deltaX = event.clientX - startX.value;
    const newWidth = startWidth.value - deltaX;
    codeServerStore.setPanelWidth(newWidth);
}

function stopCodeServerResize() {
    isDraggingCodeServerSeparator.value = false;
}

function closeCodeServerPanel() {
    codeServerStore.closePanel();
}

// life cycle
onMounted(() => {
    // Using a custom event here which, in contrast to watching $route,
    // always fires when a route is pushed instead of validating it first.
    router.app.$on("router-push", hideCenter);

    // Add global resize listeners
    document.addEventListener("mousemove", handleCodeServerResize);
    document.addEventListener("mouseup", stopCodeServerResize);
});

onUnmounted(() => {
    router.app.$off("router-push", hideCenter);
    document.removeEventListener("mousemove", handleCodeServerResize);
    document.removeEventListener("mouseup", stopCodeServerResize);
});
</script>

<template>
    <div id="columns" class="d-flex">
        <ActivityBar v-if="showPanels" />
        <div id="center" class="overflow-auto p-3 w-100">
            <CenterFrame v-show="showCenter" id="galaxy_main" @load="onLoad" />
            <div v-show="!showCenter" class="h-100">
                <router-view :key="$route.fullPath" class="h-100" />
            </div>
        </div>

        <!-- Code-Server Separator -->
        <button
            v-if="showPanel && showPanels"
            type="button"
            class="code-server-separator"
            :class="{ dragging: isDraggingCodeServerSeparator }"
            aria-label="Resize editor panel"
            title="Drag to resize editor panel"
            @mousedown="startCodeServerResize" />

        <!-- Code-Server Panel -->
        <div v-if="showPanel && showPanels" class="code-server-panel-wrapper" :style="{ width: `${panelWidth}px` }">
            <CodeServerPanel :tool="currentTool" @close="closeCodeServerPanel" />
        </div>

        <!-- History Panel -->
        <FlexPanel v-if="showPanels" side="right" :reactive-width.sync="historyPanelWidth">
            <HistoryIndex />
        </FlexPanel>

        <DragAndDropModal />
    </div>
</template>

<style scoped>
#columns {
    height: 100%;
}

#center {
    flex: 1;
    min-width: 0;
    overflow: auto !important;
}

.code-server-panel-wrapper {
    display: flex;
    flex-direction: column;
    flex-shrink: 0;
    border-left: 1px solid #e0e0e0;
    background-color: #1e1e1e;
    position: relative;
}

.code-server-separator {
    width: 4px;
    height: 100%;
    cursor: col-resize;
    background-color: #e0e0e0;
    border: none;
    border-left: 1px solid #d0d0d0;
    border-right: 1px solid #f0f0f0;
    flex-shrink: 0;
    padding: 0;
    transition: background-color 0.2s;
}

.code-server-separator:hover,
.code-server-separator.dragging {
    background-color: #0078d4;
}
</style>
