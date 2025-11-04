<script setup lang="ts">
import { onMounted } from "vue";

import type { WorkflowInvocation } from "@/api/invocations";
import Webhooks from "@/utils/webhooks";
import { startWatchingHistory } from "@/watch/watchHistoryProvided";

import GridInvocation from "@/components/Grid/GridInvocation.vue";
import WorkflowInvocationState from "@/components/WorkflowInvocationState/WorkflowInvocationState.vue";

const props = defineProps<{
    workflowName: string;
    invocations: WorkflowInvocation[];
}>();

const emit = defineEmits<{
    (e: "backToEditor"): void;
}>();

onMounted(() => {
    new Webhooks.WebhookView({
        type: "workflow",
        toolId: null,
        toolVersion: null,
    });
    startWatchingHistory();
});

const targetHistories = props.invocations.reduce((histories, invocation) => {
    if (invocation.history_id && !histories.includes(invocation.history_id)) {
        histories.push(invocation.history_id);
    }
    return histories;
}, [] as string[]);
</script>

<template>
    <div class="workflow-run-success">
        <div class="success-header">
            <button class="back-button" @click="() => emit('backToEditor')" title="Return to workflow editor">
                ← Back to Editor
            </button>
        </div>
        <div>
            <div v-if="props.invocations.length > 1" class="donemessagelarge">
                Successfully invoked workflow <b>{{ props.workflowName }}</b>
                <em> - {{ props.invocations.length }} times</em>.
                <span v-if="targetHistories.length > 1">
                    This workflow will generate results in multiple histories. You can observe progress in the
                    <router-link to="/histories/view_multiple">history multi-view</router-link>.
                </span>
            </div>
            <GridInvocation v-if="props.invocations.length > 1" :invocations-list="props.invocations" />
            <WorkflowInvocationState
                v-else-if="props.invocations.length === 1 && props.invocations[0]"
                :invocation-id="props.invocations[0].id"
                is-full-page
                success />
            <div id="webhook-view"></div>
        </div>
    </div>
</template>

<style scoped>
.workflow-run-success {
    display: flex;
    flex-direction: column;
    height: 100%;
}

.success-header {
    padding: 12px;
    border-bottom: 1px solid #e0e0e0;
    background-color: #f9f9f9;
}

.back-button {
    padding: 6px 12px;
    background-color: #f0f0f0;
    border: 1px solid #ccc;
    border-radius: 4px;
    cursor: pointer;
    font-size: 13px;
    color: #333;
    transition: all 0.2s ease;
}

.back-button:hover {
    background-color: #e0e0e0;
    border-color: #999;
}

.back-button:active {
    background-color: #d0d0d0;
}
</style>
