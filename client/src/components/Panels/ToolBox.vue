<script setup lang="ts">
import { library } from "@fortawesome/fontawesome-svg-core";
import { faEye, faEyeSlash } from "@fortawesome/free-regular-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import { storeToRefs } from "pinia";
import { computed, type ComputedRef, type PropType, type Ref, ref, watch } from "vue";

import { useGlobalUploadModal } from "@/composables/globalUploadModal";
import { useToolRouting } from "@/composables/route";
import type { Tool, ToolSection as ToolSectionType } from "@/stores/toolStore";
import { useToolStore } from "@/stores/toolStore";
import localize from "@/utils/localization";

import { filterTools, getValidPanelItems, getValidToolsInCurrentView, getValidToolsInEachSection } from "./utilities";

import ToolSearch from "./Common/ToolSearch.vue";
import ToolSection from "./Common/ToolSection.vue";

const SECTION_IDS_TO_EXCLUDE = ["expression_tools"]; // if this isn't the Workflow Editor panel

const { openGlobalUploadModal } = useGlobalUploadModal();
const { routeToTool } = useToolRouting();

const emit = defineEmits<{
    (e: "update:show-advanced", showAdvanced: boolean): void;
    (e: "update:panel-query", query: string): void;
    (e: "onInsertTool", toolId: string, toolName: string): void;
    (e: "onInsertModule", moduleName: string, moduleTitle: string | undefined): void;
    (e: "onCreateTool"): void;
    (e: "onDeleteTool", toolId: string): void;
    (e: "onEditTool", toolId: string, toolName: string): void;
    (e: "onOpenTool", tool: Tool): void;
}>();

const props = defineProps({
    workflow: { type: Boolean, default: false },
    showAdvanced: { type: Boolean, default: false, required: true },
    panelQuery: { type: String, required: true },
    dataManagers: { type: Array, default: null },
    moduleSections: { type: Array as PropType<Record<string, any>>, default: null },
    useSearchWorker: { type: Boolean, default: true },
});

library.add(faEye, faEyeSlash);

const queryFilter: Ref<string | null> = ref(null);
const queryPending = ref(false);
const showSections = ref(props.workflow);
const results: Ref<string[]> = ref([]);
const resultPanel: Ref<Record<string, Tool | ToolSectionType> | null> = ref(null);
const closestTerm: Ref<string | null> = ref(null);

// Delete confirmation modal state
const showDeleteModal = ref(false);
const deleteToolId = ref("");
const deleteToolName = ref("");
const isDeletingTool = ref(false);
const deleteStatus = ref("");
const deleteCheckCount = ref(0);

const toolStore = useToolStore();

const propShowAdvanced = computed({
    get: () => {
        return props.showAdvanced;
    },
    set: (val: boolean) => {
        emit("update:show-advanced", val);
    },
});
const query = computed({
    get: () => {
        return props.panelQuery.trim();
    },
    set: (q: string) => {
        queryPending.value = true;
        emit("update:panel-query", q);
    },
});

const { currentPanelView, currentToolSections } = storeToRefs(toolStore);
const hasResults = computed(() => results.value.length > 0);
const queryTooShort = computed(() => query.value && query.value.length < 3);
const queryFinished = computed(() => query.value && queryPending.value != true);

// Watch for when store tool sections are refreshed (after deletion)
watch(
    () => currentToolSections.value,
    () => {
        // Clear cached search results so fresh data is shown
        results.value = [];
        resultPanel.value = null;
        queryFilter.value = null;
        queryPending.value = false;
        query.value = "";
    },
    { deep: true }
);

const hasDataManagerSection = computed(() => props.workflow && props.dataManagers && props.dataManagers.length > 0);
const dataManagerSection = computed(() => {
    const dynamicSection: ToolSectionType = {
        model_class: "ToolSection",
        id: "__data_managers",
        name: localize("Data Managers"),
        elems: props.dataManagers as Tool[],
    };
    return dynamicSection;
});

/** `toolsById` from `toolStore`, except it only has valid tools for `props.workflow` value */
const localToolsById = computed(() => {
    if (toolStore.toolsById && Object.keys(toolStore.toolsById).length > 0) {
        return getValidToolsInCurrentView(
            toolStore.toolsById,
            props.workflow,
            !props.workflow ? SECTION_IDS_TO_EXCLUDE : []
        );
    }
    return {};
});

/** `currentPanel` from `toolStore`, except it only has valid tools and sections for `props.workflow` value */
const localSectionsById = computed(() => {
    const validToolIdsInCurrentView = Object.keys(localToolsById.value);

    // Looking within each `ToolSection`, and filtering on child elements
    const sectionEntries = getValidToolsInEachSection(validToolIdsInCurrentView, currentToolSections.value);

    // Looking at each item in the panel now (not within each child)
    return getValidPanelItems(
        sectionEntries,
        validToolIdsInCurrentView,
        !props.workflow ? SECTION_IDS_TO_EXCLUDE : []
    ) as Record<string, Tool | ToolSectionType>;
});

const toolsList = computed(() => Object.values(localToolsById.value));

function onCreateToolClick() {
    emit("onCreateTool");
}

/**
 * If not searching or no results, we show all tools in sections (default)
 *
 * If we have results for search, we show tools in sections or just tools,
 * based on whether `showSections` is true or false
 */
const localPanel: ComputedRef<Record<string, Tool | ToolSectionType> | null> = computed(() => {
    if (hasResults.value) {
        if (showSections.value) {
            return resultPanel.value;
        } else {
            return filterTools(localToolsById.value, results.value) as Record<string, Tool | ToolSectionType>;
        }
    } else {
        return localSectionsById.value;
    }
});

const buttonIcon = computed(() => (showSections.value ? faEyeSlash : faEye));
const buttonText = computed(() => (showSections.value ? localize("Hide Sections") : localize("Show Sections")));

function onInsertModule(module: Record<string, any>, event: Event) {
    event.preventDefault();
    emit("onInsertModule", module.name, module.title);
}

function onToolClick(tool: Tool, evt: Event) {
    if (!props.workflow) {
        if (tool.id === "upload1") {
            evt.preventDefault();
            openGlobalUploadModal();
        } else if (tool.form_style === "regular") {
            evt.preventDefault();
            // encode spaces in tool.id
            routeToTool(tool.id);
        }
    } else {
        evt.preventDefault();
        emit("onInsertTool", tool.id, tool.name);
    }
}

function onResults(
    idResults: string[] | null,
    sectioned: Record<string, Tool | ToolSectionType> | null,
    closestMatch: string | null = null
) {
    if (idResults !== null && idResults.length > 0) {
        results.value = idResults;
        resultPanel.value = sectioned;
        if (sectioned === null) {
            showSections.value = false;
        }
    } else {
        results.value = [];
        resultPanel.value = null;
    }
    closestTerm.value = closestMatch;
    queryFilter.value = hasResults.value ? query.value : null;
    queryPending.value = false;
}

function onSectionFilter(filter: string) {
    if (query.value !== filter) {
        query.value = filter;
        if (!showSections.value) {
            onToggle();
        }
    } else {
        query.value = "";
    }
}

function onToggle() {
    showSections.value = !showSections.value;
}

function onEditToolClick(tool: Tool) {
    emit("onEditTool", tool.id, tool.name);
}

function onDeleteToolClick(tool: Tool) {
    deleteToolId.value = tool.id;
    deleteToolName.value = tool.name;
    showDeleteModal.value = true;
    isDeletingTool.value = false;
    deleteStatus.value = "";
    deleteCheckCount.value = 0;
}

async function confirmDeleteTool() {
    if (!deleteToolId.value) return;

    isDeletingTool.value = true;
    deleteStatus.value = "Deleting tool...";
    deleteCheckCount.value = 0;

    try {
        // Emit delete event to parent (ToolPanel)
        emit("onDeleteTool", deleteToolId.value);

        // Poll to verify tool is actually deleted
        const maxAttempts = 30; // 30 checks
        const pollInterval = 500; // 500ms between checks

        while (deleteCheckCount.value < maxAttempts) {
            deleteCheckCount.value++;
            await new Promise(resolve => setTimeout(resolve, pollInterval));

            // Check if tool still exists in the tool list
            const toolExists = toolStore.toolsById && toolStore.toolsById[deleteToolId.value];

            deleteStatus.value = `Waiting for new tool list to be loading...`;

            if (!toolExists) {
                deleteStatus.value = "✓ Tool deleted successfully!";
                isDeletingTool.value = false;
                // Auto-close modal after 1 second
                setTimeout(() => {
                    showDeleteModal.value = false;
                }, 1000);
                return;
            }
        }

        // If we get here, tool still exists after max attempts
        deleteStatus.value = "Tool deletion may not have completed. Closing modal...";
        isDeletingTool.value = false;
        setTimeout(() => {
            showDeleteModal.value = false;
        }, 2000);

    } catch (error) {
        deleteStatus.value = `Error: ${error instanceof Error ? error.message : "Failed to delete tool"}`;
        isDeletingTool.value = false;
    }
}

async function onOpenToolClick(tool: Tool) {
    emit("onOpenTool", tool);
}
</script>

<template>
    <div class="unified-panel" data-description="panel toolbox">
        <div class="unified-panel-controls">
            <ToolSearch
                :enable-advanced="!props.workflow"
                :current-panel-view="currentPanelView"
                :placeholder="localize('search tools')"
                :show-advanced.sync="propShowAdvanced"
                :tools-list="toolsList"
                :current-panel="localSectionsById"
                :query="query"
                :query-pending="queryPending"
                :use-worker="useSearchWorker"
                @onQuery="(q) => (query = q)"
                @onResults="onResults" />
            <section v-if="!propShowAdvanced">
                <div v-if="hasResults && resultPanel" class="pb-2">
                    <b-button size="sm" class="w-100" @click="onToggle">
                        <FontAwesomeIcon :icon="buttonIcon" />
                        <span class="mr-1">{{ buttonText }}</span>
                    </b-button>
                </div>
                <div v-else-if="queryTooShort" class="pb-2">
                    <b-badge class="alert-info w-100">Search term is too short</b-badge>
                </div>
                <div v-else-if="queryFinished && !hasResults" class="pb-2">
                    <b-badge class="alert-warning w-100">No results found</b-badge>
                </div>
                <div v-if="closestTerm" class="pb-2">
                    <b-badge class="alert-danger w-100">
                        Did you mean:
                        <i>
                            <a href="javascript:void(0)" @click="query = closestTerm">{{ closestTerm }}</a>
                        </i>
                        ?
                    </b-badge>
                </div>
            </section>
        </div>
        <div v-if="!propShowAdvanced" class="unified-panel-body">
            <div class="toolMenuContainer">
                <div v-if="localPanel" class="toolMenu">
                    <div v-if="props.workflow">
                        <ToolSection
                            v-for="category in moduleSections"
                            :key="category.name"
                            :hide-name="true"
                            :category="category"
                            tool-key="name"
                            :section-name="category.name"
                            :query-filter="queryFilter || undefined"
                            :disable-filter="true"
                            @onClick="onInsertModule" />
                    </div>
                    <ToolSection
                        v-if="hasDataManagerSection"
                        :category="dataManagerSection"
                        :query-filter="queryFilter || undefined"
                        :disable-filter="true"
                        @onClick="onToolClick" />
                    <div v-for="(panel, key) in localPanel" :key="key">
                        <ToolSection
                            v-if="panel"
                            :category="panel || {}"
                            :query-filter="queryFilter || undefined"
                            :has-filter-button="hasResults && currentPanelView === 'default'"
                            :show-tool-actions="true"
                            @onClick="onToolClick"
                            @onFilter="onSectionFilter"
                            @onEditTool="onEditToolClick"
                            @onDeleteTool="onDeleteToolClick"
                            @onOpenTool="onOpenToolClick" />
                    </div>
                </div>
            </div>

            <b-button id="create-tool-button" size="sm" @click="onCreateToolClick">Create tool</b-button>
        </div>

        <!-- Delete Tool Confirmation Modal -->
        <b-modal
            id="delete-tool-modal"
            v-model="showDeleteModal"
            title="Delete Tool"
            :no-close-on-backdrop="isDeletingTool"
            :no-close-on-esc="isDeletingTool"
            @hidden="() => { showDeleteModal = false; }">
            <template v-slot:modal-title>
                <h2 class="mb-0">Delete Tool</h2>
            </template>
            <div class="mb-3">
                <p>Are you sure you want to delete the tool "<strong>{{ deleteToolName }}</strong>"?</p>
                <b-alert v-if="deleteStatus" variant="info" show>
                    {{ deleteStatus }}
                </b-alert>
            </div>
            <template v-slot:modal-footer>
                <b-button
                    variant="secondary"
                    :disabled="isDeletingTool"
                    @click="showDeleteModal = false">
                    Cancel
                </b-button>
                <b-button
                    variant="danger"
                    :disabled="isDeletingTool"
                    @click="confirmDeleteTool">
                    <span v-if="isDeletingTool">Deleting...</span>
                    <span v-else>Delete</span>
                </b-button>
            </template>
        </b-modal>
    </div>
</template>

<style scoped>
.toolTitle {
    overflow-wrap: anywhere;
}
#create-tool-button {
    display: block;
    margin-left: auto;
    margin-right: auto;
    margin-top: 10px;
    margin-bottom: 10px;
}
</style>
