<script setup lang="ts">
import { faCaretDown } from "@fortawesome/free-solid-svg-icons";
import { FontAwesomeIcon } from "@fortawesome/vue-fontawesome";
import axios from "axios";
import { storeToRefs } from "pinia";
import { computed, ref, watch } from "vue";

import { getAppRoot } from "@/onload/loadConfig";
import { useToolStore } from "@/stores/toolStore";
import { useUserStore } from "@/stores/userStore";
import { useCodeServerStore } from "@/stores/codeServerStore";
import localize from "@/utils/localization";
import { errorMessageAsString } from "@/utils/simple-error";

import { types_to_icons } from "./utilities";

import LoadingSpan from "../LoadingSpan.vue";
import FavoritesButton from "./Buttons/FavoritesButton.vue";
import PanelViewMenu from "./Menus/PanelViewMenu.vue";
import ToolBox from "./ToolBox.vue";
import Heading from "@/components/Common/Heading.vue";

const toolStore = useToolStore();

const userStore = useUserStore();
const props = defineProps({
    dataManagers: { type: Array, default: null },
    moduleSections: { type: Array, default: null },
    useSearchWorker: { type: Boolean, default: true },
    workflow: { type: Boolean, default: false },
});

const emit = defineEmits<{
    (e: "onInsertModule", moduleName: string, moduleTitle: string | undefined): void;
    (e: "onInsertTool", toolId: string, toolName: string): void;
    (e: "onInsertWorkflow", workflowLatestId: string | undefined, workflowName: string): void;
    (e: "onInsertWorkflowSteps", workflowId: string, workflowStepCount: number | undefined): void;
}>();

const { currentPanelView, currentToolSections, isPanelPopulated, loading, panels, toolSections } =
    storeToRefs(toolStore);

const errorMessage = ref("");
const panelName = ref("");
const panelsFetched = ref(false);
const query = ref("");
const showAdvanced = ref(false);

// Create tool modal state
const showCreateModal = ref(false);
const newToolName = ref("");
const createError = ref<string | null>(null);
const createSuccess = ref(false);
const isCreatingTool = ref(false);
const createInputRef = ref<any>(null);
const createForbiddenCharWarning = ref(false);

// Edit tool modal state
const showEditModal = ref(false);
const editToolId = ref("");
const editToolName = ref("");
const editError = ref<string | null>(null);
const editSuccess = ref(false);
const isEditingTool = ref(false);
const editInputRef = ref<any>(null);
const editForbiddenCharWarning = ref(false);

// CodeServer store
const codeServerStore = useCodeServerStore();

const panelIcon = computed(() => {
    if (showAdvanced.value) {
        return "search";
    } else if (
        currentPanelView.value !== "default" &&
        panels.value &&
        typeof panels.value[currentPanelView.value]?.view_type === "string"
    ) {
        const viewType = panels.value[currentPanelView.value]?.view_type;
        return viewType ? types_to_icons[viewType] : null;
    } else {
        return null;
    }
});

const showFavorites = computed({
    get() {
        return query.value.includes("#favorites");
    },
    set(value) {
        if (value) {
            if (!query.value.includes("#favorites")) {
                query.value = `#favorites ${query.value}`.trim();
            }
        } else {
            query.value = query.value.replace("#favorites", "").trim();
        }
    },
});

// Tool validation computed properties
const allTools = computed(() => {
    const { toolsById } = toolStore;
    return toolsById ? Object.values(toolsById) : [];
});

const validToolName = computed(() => {
    const name = newToolName.value || "";
    const exists = allTools.value.some(element => element.id === newToolName.value);
    // allow alphanumeric, underscore, space, hyphen, dot
    return /^[\w \-.]+$/.test(name) && name.trim().length > 0 && !exists;
});

const validEditToolName = computed(() => {
    const name = editToolName.value || "";
    // allow alphanumeric, underscore, space, hyphen, dot
    return /^[\w \-.]+$/.test(name) && name.trim().length > 0;
});

const toolPanelHeader = computed(() => {
    if (showAdvanced.value) {
        return localize("Advanced Tool Search");
    } else if (loading.value && panelName.value) {
        return localize(panelName.value);
    } else if (currentPanelView.value !== "default" && panels.value && panels.value[currentPanelView.value]?.name) {
        return localize(panels.value[currentPanelView.value]?.name);
    } else {
        return localize("Tools");
    }
});

async function initializePanel() {
    try {
        await userStore.loadUser(false);
        await toolStore.fetchPanels();
        await toolStore.fetchTools();
        await toolStore.initializePanel();
    } catch (error) {
        console.error(`ToolPanel::initializePanel - ${error}`);
        errorMessage.value = errorMessageAsString(error);
    } finally {
        panelsFetched.value = true;
    }
}

async function updatePanelView(panelView: string) {
    panelName.value = panels.value[panelView]?.name || "";
    await toolStore.setPanel(panelView);
    panelName.value = "";
}

function onInsertModule(moduleName: string, moduleTitle: string | undefined) {
    emit("onInsertModule", moduleName, moduleTitle);
}

function onInsertTool(toolId: string, toolName: string) {
    emit("onInsertTool", toolId, toolName);
}

function onInsertWorkflow(workflowId: string | undefined, workflowName: string) {
    emit("onInsertWorkflow", workflowId, workflowName);
}

function onInsertWorkflowSteps(workflowId: string, workflowStepCount: number | undefined) {
    emit("onInsertWorkflowSteps", workflowId, workflowStepCount);
}

function onToolNameInput(val: string) {
    // remove any characters that aren't allowed as the user types
    const filtered = (val || "").replace(/[^\w \-.]/g, "");
    // Check if any characters were removed
    if (filtered !== val) {
        createForbiddenCharWarning.value = true;
        // Auto-hide warning after 2 seconds
        setTimeout(() => {
            createForbiddenCharWarning.value = false;
        }, 2000);
    }
    newToolName.value = filtered;
    createError.value = null;
}

function onEditToolNameInput(val: string) {
    // remove any characters that aren't allowed as the user types
    const filtered = (val || "").replace(/[^\w \-.]/g, "");
    // Check if any characters were removed
    if (filtered !== val) {
        editForbiddenCharWarning.value = true;
        // Auto-hide warning after 2 seconds
        setTimeout(() => {
            editForbiddenCharWarning.value = false;
        }, 2000);
    }
    editToolName.value = filtered;
    editError.value = null;
}

async function confirmCreateTool() {
    if (createSuccess.value) {
        showCreateModal.value = false;
        return;
    }
    if (!validToolName.value) {
        createError.value = "Invalid tool name";
        return;
    }
    isCreatingTool.value = true;
    try {
        const url = `${getAppRoot()}api/tools/create_tool_config/`;
        // Replace spaces with underscores for the tool ID
        const toolId = newToolName.value.replace(/\s+/g, '_').toLowerCase();
        await axios.post(url, { name: newToolName.value, id: toolId });
        // success - show feedback and keep modal open
        createSuccess.value = true;
        createError.value = null;
        isCreatingTool.value = false;

        // Refresh the tool list so the new tool appears (do this first)
        await refreshToolsAndPanel();

        // Auto-close modal after 2 seconds (after refresh completes and success is visible)
        setTimeout(() => {
            showCreateModal.value = false;
        }, 2000);
    } catch (e) {
        // basic error reporting - keep modal open so user can retry
        let errorMessage = "Failed to create tool";
        if (axios.isAxiosError(e)) {
            const status = e.response?.status;
            const statusText = e.response?.statusText;
            // Check for error message in multiple possible locations
            const errorData = e.response?.data?.error || e.response?.data?.message || e.response?.data?.err_msg;
            if (errorData) {
                errorMessage = typeof errorData === 'string' ? errorData : JSON.stringify(errorData);
            } else if (statusText) {
                errorMessage = `${statusText}${status ? ` (${status})` : ''}`;
            } else {
                errorMessage = e.message || errorMessage;
            }
        } else if (e instanceof Error) {
            errorMessage = e.message;
        }
        console.error("Create tool error:", errorMessage, e);
        createError.value = errorMessage;
        createSuccess.value = false;
        isCreatingTool.value = false;
    }
}

async function confirmEditTool() {
    if (editSuccess.value) {
        showEditModal.value = false;
        return;
    }
    if (!validEditToolName.value) {
        editError.value = "Invalid tool name";
        return;
    }
    isEditingTool.value = true;
    try {
        const url = `${getAppRoot()}api/tools/edit_tool_config/`;
        await axios.post(url, { id: editToolId.value, name: editToolName.value });
        // success - show feedback and keep modal open
        editSuccess.value = true;
        editError.value = null;
        isEditingTool.value = false;

        // Refresh the tool list so the updated tool appears (do this first)
        await refreshToolsAndPanel();

        // Auto-close modal after 2 seconds (after refresh completes and success is visible)
        setTimeout(() => {
            showEditModal.value = false;
        }, 2000);
    } catch (e) {
        // basic error reporting - keep modal open so user can retry
        let errorMessage = "Failed to edit tool";
        if (axios.isAxiosError(e)) {
            const status = e.response?.status;
            const statusText = e.response?.statusText;
            const message = e.response?.data?.message || e.response?.data?.err_msg;
            errorMessage = message || (statusText ? `${statusText} (${status})` : e.message || errorMessage);
        } else if (e instanceof Error) {
            errorMessage = e.message;
        }
        console.error("Edit tool error:", errorMessage, e);
        editError.value = errorMessage;
        editSuccess.value = false;
        isEditingTool.value = false;
    }
}

async function refreshToolsAndPanel() {
    // Clear cached tools so fetchTools will re-fetch the full tool list
    toolStore.saveAllTools([]);
    // Determine which panel view we need to clear (don't overwrite the empty-string key)
    const viewToClear = currentPanelView.value || toolStore.defaultPanelView || "";
    // Clear the actual panel's sections so they will be re-fetched by initializePanel
    toolStore.saveToolSections(viewToClear, {});
    // Re-initialize panel to load fresh tools
    await initializePanel();
}

function onCreateToolClicked() {
    // Reset state when opening modal
    showCreateModal.value = true;
    newToolName.value = "";
    createError.value = null;
    createSuccess.value = false;
    isCreatingTool.value = false;
}

function onEditToolClicked(toolId: string, toolName: string) {
    // Reset state when opening modal
    showEditModal.value = true;
    editToolId.value = toolId;
    editToolName.value = toolName;
    editError.value = null;
    editSuccess.value = false;
    isEditingTool.value = false;
}

async function onDeleteTool(toolId: string) {
    try {
        const url = `${getAppRoot()}api/tools/delete_tool_config/`;
        await axios.post(url, { id: toolId });
        // Refresh the tool list
        await refreshToolsAndPanel();
    } catch (e) {
        alert((e as Error).message || "Failed to delete tool");
    }
}

async function onOpenTool(tool: any) {
    try {
        // Call the API to open the tool in a code editor
        const url = `${getAppRoot()}api/tools/open_tool_in_code_editor/`;
        const response = await axios.post(url, { id: tool.id });
        // API returns [message, "done"] tuple - extract the first element
        const data = Array.isArray(response.data) ? response.data[0] : response.data;

        // If external_editor is false (or not set), open the frontend code-server panel
        // If external_editor is true, an external editor was launched, so don't open the panel
        if (!data.external_editor) {
            codeServerStore.openPanel(tool, data);
        }
    } catch (e) {
        console.error("Failed to open tool in code editor:", e);
        // On error, fall back to opening the frontend panel
        codeServerStore.openPanel(tool);
    }
}

watch(
    () => query.value,
    (newQuery) => {
        showFavorites.value = newQuery.includes("#favorites");
    }
);

// if currentPanelView ever becomes null || "", load tools
watch(
    () => currentPanelView.value,
    async (newVal) => {
        query.value = "";
        if ((!newVal || !toolSections.value[newVal]) && panelsFetched.value) {
            await initializePanel();
        }
    }
);

// Focus create input when modal opens
watch(
    () => showCreateModal.value,
    (isOpen) => {
        if (isOpen) {
            setTimeout(() => {
                createInputRef.value?.$el?.focus?.();
            }, 0);
        }
    }
);

// Focus edit input when modal opens
watch(
    () => showEditModal.value,
    (isOpen) => {
        if (isOpen) {
            setTimeout(() => {
                editInputRef.value?.$el?.focus?.();
            }, 0);
        }
    }
);

initializePanel();
</script>

<template>
    <div v-if="panelsFetched" id="toolbox-panel" class="unified-panel" aria-labelledby="toolbox-heading">
        <div unselectable="on">
            <div class="unified-panel-header-inner mx-3 my-2 d-flex justify-content-between">
                <PanelViewMenu
                    v-if="panels && Object.keys(panels).length > 1"
                    :panel-views="panels"
                    :current-panel-view="currentPanelView"
                    :show-advanced.sync="showAdvanced"
                    :store-loading="loading"
                    @updatePanelView="updatePanelView">
                    <template v-slot:panel-view-selector>
                        <div class="d-flex justify-content-between panel-view-selector">
                            <div>
                                <span
                                    v-if="panelIcon && !loading"
                                    :class="['fas', `fa-${panelIcon}`, 'mr-1']"
                                    data-description="panel view header icon" />
                                <Heading
                                    id="toolbox-heading"
                                    :class="!showAdvanced && toolPanelHeader !== 'Tools' && 'font-italic'"
                                    h2
                                    inline
                                    size="sm">
                                    <span v-if="loading && panelName">
                                        <LoadingSpan :message="toolPanelHeader" />
                                    </span>
                                    <span v-else>{{ toolPanelHeader }}</span>
                                </Heading>
                            </div>
                            <div v-if="!showAdvanced" class="panel-header-buttons">
                                <FontAwesomeIcon :icon="faCaretDown" />
                            </div>
                        </div>
                    </template>
                </PanelViewMenu>
                <div v-if="!showAdvanced" class="panel-header-buttons">
                    <FavoritesButton v-model="showFavorites" />
                </div>
            </div>
        </div>
        <!-- <button @click="()=> onCreateNewTool('')">RESET BUTTON</button> -->
        <ToolBox
            v-if="isPanelPopulated"
            :workflow="props.workflow"
            :panel-query.sync="query"
            :show-advanced.sync="showAdvanced"
            :data-managers="dataManagers"
            :module-sections="moduleSections"
            :use-search-worker="useSearchWorker"
            @onInsertTool="onInsertTool"
            @onInsertModule="onInsertModule"
            @onInsertWorkflow="onInsertWorkflow"
            @onInsertWorkflowSteps="onInsertWorkflowSteps"
            @onCreateTool="onCreateToolClicked"
            @onEditTool="onEditToolClicked"
            @onDeleteTool="onDeleteTool"
            @onOpenTool="onOpenTool"
            />
        <div v-else-if="errorMessage" data-description="tool panel error message">
            <b-alert class="m-2" variant="danger" show>
                {{ errorMessage }}
            </b-alert>
        </div>
        <div v-else>
            <b-badge class="alert-info w-100">
                <LoadingSpan message="Loading Toolbox" />
            </b-badge>
        </div>

        <!-- Create Tool Modal (persists across ToolBox re-renders) -->
        <b-modal
            id="create-tool-modal"
            v-model="showCreateModal"
            title="Create tool"
            @hidden="() => { showCreateModal = false; }">
            <template v-slot:modal-title>
                <h2 class="mb-0">Tool name</h2>
            </template>
            <div class="mb-2">
                <b-alert v-show="createSuccess" variant="success" class="mb-2" show>
                    ✓ Tool created successfully!
                </b-alert>

                <b-alert
                    v-show="createError"
                    variant="danger"
                    dismissible
                    class="mb-2"
                    show
                    @dismissed="createError = null"
                >
                    {{ createError }}
                </b-alert>

                <b-alert
                    v-show="createForbiddenCharWarning"
                    variant="warning"
                    class="mb-2"
                    show
                >
                    ⚠ Special characters are not allowed and will be removed
                </b-alert>

                <b-form-input
                    v-show="!createSuccess"
                    ref="createInputRef"
                    v-model="newToolName"
                    placeholder="Enter tool name"
                    :disabled="isCreatingTool"
                    @input="onToolNameInput($event)"
                    @keydown.enter="confirmCreateTool"
                />
                <small v-if="!createError && !createSuccess && !isCreatingTool" class="text-muted">Allowed characters: letters, numbers, spaces, underscore, hyphen, dot</small>
            </div>
            <template v-slot:modal-footer>
                <b-button v-show="!createSuccess && !isCreatingTool" variant="secondary" :disabled="isCreatingTool" @click="showCreateModal = false">{{ 'Cancel' }}</b-button>
                <b-button variant="primary" :disabled="!validToolName || isCreatingTool" @click="confirmCreateTool">
                    <span v-if="isCreatingTool">Creating...</span>
                    <span v-else-if="createSuccess">Done</span>
                    <span v-else>Create</span>
                </b-button>
            </template>
        </b-modal>

        <!-- Edit Tool Modal (persists across ToolBox re-renders) -->
        <b-modal
            id="edit-tool-modal"
            v-model="showEditModal"
            title="Edit tool"
            @hidden="() => { showEditModal = false; }">
            <template v-slot:modal-title>
                <h2 class="mb-0">Edit tool name</h2>
            </template>
            <div class="mb-2">
                <b-alert v-show="editSuccess" variant="success" class="mb-2" show>
                    ✓ Tool updated successfully!
                </b-alert>
                <b-alert
                    v-show="editError"
                    variant="danger"
                    dismissible
                    class="mb-2"
                    show
                    @dismissed="editError = null"
                >
                    {{ editError }}
                </b-alert>

                <b-alert
                    v-show="editForbiddenCharWarning"
                    variant="warning"
                    class="mb-2"
                    show
                >
                    ⚠ Special characters are not allowed and were removed
                </b-alert>

                <b-form-input
                    v-if="!editSuccess"
                    ref="editInputRef"
                    v-model="editToolName"
                    placeholder="Enter tool name"
                    :disabled="isEditingTool"
                    @input="onEditToolNameInput($event)"
                    @keydown.enter="confirmEditTool"
                />
                <small v-if="!editError && !editSuccess && !isEditingTool" class="text-muted">Allowed characters: letters, numbers, spaces, underscore, hyphen, dot</small>
            </div>
            <template v-slot:modal-footer>
                <b-button variant="secondary" :disabled="isEditingTool" @click="showEditModal = false">{{ editSuccess ? 'Close' : 'Cancel' }}</b-button>
                <b-button variant="primary" :disabled="!validEditToolName || isEditingTool" @click="confirmEditTool">
                    <span v-if="isEditingTool">Saving...</span>
                    <span v-else-if="editSuccess">Done</span>
                    <span v-else>Save</span>
                </b-button>
            </template>
        </b-modal>
    </div>
    <b-alert v-else-if="currentToolSections" class="m-2" variant="info" show>
        <LoadingSpan message="Loading Toolbox" />
    </b-alert>
</template>

<style lang="scss" scoped>
@import "theme/blue.scss";

.panel-view-selector {
    color: $panel-header-text-color;
}
</style>
