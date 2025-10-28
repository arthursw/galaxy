<template>
    <div class="toolTitle">
        <a v-if="tool.disabled" :data-tool-id="tool.id" class="title-link name text-muted">
            <span v-if="!hideName">{{ tool.name }}</span>
            <span class="description">{{ tool.description }}</span>
        </a>
        <div v-else class="d-flex align-items-center">
            <a
                :class="targetClass"
                :data-tool-id="tool.id"
                :href="tool.link"
                :target="tool.target"
                :title="tool.help"
                class="flex-grow-1"
                @click="onClick">
                <span class="labels">
                    <span
                        v-for="(label, index) in tool.labels"
                        :key="index"
                        :class="['badge', 'badge-primary', `badge-${label}`]">
                        {{ label }}
                    </span>
                </span>
                <span v-if="!hideName" class="name font-weight-bold">{{ tool.name }}</span>
                <span class="description">{{ tool.description }}</span>
                <span
                    v-b-tooltip.hover
                    :class="['operation', 'float-right', operationIcon]"
                    :title="operationTitle"
                    @click.stop.prevent="onOperation" />
            </a>
            <div v-if="showToolActions" class="tool-actions ml-2">
                <button
                    v-b-tooltip.hover
                    class="btn btn-sm btn-link p-0 mr-1"
                    title="Open in VS Code"
                    @click.stop="onOpenTool">
                    📂
                </button>
                <button
                    v-b-tooltip.hover
                    class="btn btn-sm btn-link p-0 mr-1"
                    title="Rename tool"
                    @click.stop="onEditTool">
                    ✏️
                </button>
                <button
                    v-b-tooltip.hover
                    class="btn btn-sm btn-link p-0"
                    title="Delete tool"
                    @click.stop="onDeleteTool">
                    ❌
                </button>
            </div>
        </div>
    </div>
</template>

<script>
import BootstrapVue from "bootstrap-vue";
import ariaAlert from "utils/ariaAlert";
import Vue from "vue";

Vue.use(BootstrapVue);

export default {
    name: "Tool",
    props: {
        tool: {
            type: Object,
            required: true,
        },
        operationTitle: {
            type: String,
            default: "",
        },
        operationIcon: {
            type: String,
            default: "",
        },
        hideName: {
            type: Boolean,
            default: false,
        },
        toolKey: {
            type: String,
            default: "",
        },
        renderIcon: {
            type: Boolean,
            default: false,
        },
        showToolActions: {
            type: Boolean,
            default: false,
        },
    },
    computed: {
        targetClass() {
            if (this.toolKey) {
                return `tool-menu-item-${this.tool[this.toolKey]} title-link cursor-pointer`;
            } else {
                return `title-link cursor-pointer`;
            }
        },
    },
    methods: {
        onClick(evt) {
            ariaAlert(`${this.tool.name} selected from panel`);
            this.$emit("onClick", this.tool, evt);
        },
        onOperation(evt) {
            ariaAlert(`${this.tool.name} operation selected from panel`);
            this.$emit("onOperation", this.tool, evt);
        },
        onEditTool() {
            this.$emit("onEditTool", this.tool);
        },
        onDeleteTool() {
            this.$emit("onDeleteTool", this.tool);
        },
        onOpenTool() {
            this.$emit("onOpenTool", this.tool);
        },
    },
};
</script>

<style scoped>
.toolTitle {
    overflow-wrap: anywhere;
}
.tool-actions {
    display: flex;
    gap: 0.25rem;
    opacity: 0;
    transition: opacity 0.2s;
}
.toolTitle:hover .tool-actions {
    opacity: 1;
}
.tool-actions button {
    font-size: 0.875rem;
    line-height: 1;
    border: none;
    background: none;
    cursor: pointer;
}
.tool-actions button:hover {
    text-decoration: none;
    opacity: 0.7;
}
</style>
