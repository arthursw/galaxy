/**
 * Service layer for interaction for the workflow run API.
 */
import axios from "axios";
import { getAppRoot } from "onload/loadConfig";
import { rethrowSimple } from "utils/simple-error";

/**
 * Download the workflow using the 'run' style (see workflow manager on backend
 * for implementation). This contains the data needed to render the UI for workflows.
 *
 * @param {String} workflowId - (Stored?) Workflow ID to fetch data for.
 * @param {String} version - Version of the workflow to fetch.
 */
export async function getRunData(workflowId, version = null, instance = false) {
    let url = `${getAppRoot()}api/workflows/${workflowId}/download?style=run&instance=${instance}`;
    if (version) {
        url += `&version=${version}`;
    }
    try {
        const response = await axios.get(url);
        return response.data;
    } catch (e) {
        rethrowSimple(e);
    }
}

/**
 * Invoke the specified workflow using the supplied data.
 *
 * @param {String} workflowId - (Stored?) Workflow ID to fetch data for.
 */
export async function invokeWorkflow(workflowId, invocationData) {
    const url = `${getAppRoot()}api/workflows/${workflowId}/invocations`;
    const response = await axios.post(url, invocationData);
    return response.data;
}

/**
 * Request tool step data.
 *
 * @param {String} toolId - Tool ID to fetch data for.
 * @param {String} toolVersion - Corresponding tool version.
 * @param {Object} toolInputs - Current tool state.
 * @param {Object} historyId - History ID to populate data selection fields.
 */
export async function getTool(toolId, toolVersion, toolInputs, historyId) {
    const requestData = {
        tool_id: toolId,
        tool_version: toolVersion,
        inputs: JSON.parse(JSON.stringify(toolInputs)),
        history_id: historyId,
    };
    try {
        const { data } = await axios.post(`${getAppRoot()}api/tools/${toolId}/build`, requestData);
        return data;
    } catch (e) {
        rethrowSimple(e);
    }
}

/**
 * Execute workflow with Wetlands environment manager.
 *
 * @param {String} workflowId - Workflow ID to execute.
 * @param {Object} wetlandsData - Execution data including inputs and options.
 */
export async function executeWorkflowWithWetlands(workflowId, wetlandsData) {
    const url = `${getAppRoot()}api/workflows/${workflowId}/execute_with_wetlands`;
    try {
        const response = await axios.post(url, wetlandsData);
        return response.data;
    } catch (e) {
        rethrowSimple(e);
    }
}
