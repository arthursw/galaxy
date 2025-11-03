import "jest-location-mock";

import { getFakeRegisteredUser } from "@tests/test-data";
import { mount } from "@vue/test-utils";
import axios from "axios";
import MockAdapter from "axios-mock-adapter";
import flushPromises from "flush-promises";
import { createPinia } from "pinia";
import { getLocalVue } from "tests/jest/helpers";
import { ref } from "vue";

import { useServerMock } from "@/api/client/__mocks__";
import toolsList from "@/components/ToolsView/testData/toolsList.json";
import toolsListInPanel from "@/components/ToolsView/testData/toolsListInPanel.json";
import { useUserLocalStorage } from "@/composables/userLocalStorage";
import { useToolStore } from "@/stores/toolStore";

import viewsListJson from "./testData/viewsList.json";
import { types_to_icons } from "./utilities";

import ToolPanel from "./ToolPanel.vue";

interface ToolPanelView {
    id: string;
    model_class: string;
    name: string;
    description: string | null;
    view_type: string;
    searchable: boolean;
}

const localVue = getLocalVue();
const { server, http } = useServerMock();

const TEST_PANELS_URI = "/api/tool_panels";
const DEFAULT_VIEW_ID = "default";
const PANEL_VIEW_ERR_MSG = "Error loading panel view";

jest.mock("@/composables/config", () => ({
    useConfig: jest.fn(() => ({
        config: {},
        isConfigLoaded: true,
    })),
}));

jest.mock("@/composables/userLocalStorage", () => ({
    useUserLocalStorage: jest.fn(() => ref(DEFAULT_VIEW_ID)),
}));

describe("ToolPanel", () => {
    const viewsList = viewsListJson as Record<string, ToolPanelView>;

    /** Mocks and stores a non-default panel view as the current panel view */
    function storeNonDefaultView() {
        // find a view in object viewsList that is not DEFAULT_VIEW_ID
        const viewKey = Object.keys(viewsList).find((id) => id !== DEFAULT_VIEW_ID);
        if (!viewKey) {
            throw new Error("No non-default view found in viewsList");
        }
        const view = viewsList[viewKey];
        if (!view) {
            throw new Error(`View with key ${viewKey} not found in viewsList`);
        }
        // ref and useUserLocalStorage are already imported at the top
        (useUserLocalStorage as jest.Mock).mockImplementation(() => ref(viewKey));
        return { viewKey, view };
    }

    /**
     * Sets up wrapper for ToolPanel component
     * @param {String} errorView If provided, we mock an error for this view
     * @param {Boolean} failDefault If true and error view is provided, we
     *                              mock an error for the default view as well
     * @returns wrapper
     */
    async function createWrapper(errorView: string = "", failDefault: boolean = false) {
        const axiosMock = new MockAdapter(axios);
        axiosMock.onGet(`/api/tools?in_panel=False`).replyOnce(200, toolsList);
        axiosMock.onGet(TEST_PANELS_URI).reply(200, { default_panel_view: DEFAULT_VIEW_ID, views: viewsList });

        if (errorView) {
            axiosMock.onGet(`/api/tool_panels/${errorView}`).reply(400, { err_msg: PANEL_VIEW_ERR_MSG });
            if (errorView !== DEFAULT_VIEW_ID && !failDefault) {
                axiosMock.onGet(`/api/tool_panels/${DEFAULT_VIEW_ID}`).reply(200, toolsListInPanel);
            } else if (failDefault) {
                axiosMock.onGet(`/api/tool_panels/${DEFAULT_VIEW_ID}`).reply(400, { err_msg: PANEL_VIEW_ERR_MSG });
            }
        } else {
            // mock response for all panel views
            axiosMock.onGet(/\/api\/tool_panels\/.*/).reply(200, toolsListInPanel);
        }

        server.use(
            http.get("/api/users/{user_id}", ({ response }) => {
                return response(200).json(getFakeRegisteredUser());
            })
        );

        // setting this because for the default view, we just show "Tools" as the name
        // even though the backend returns "Full Tool Panel"
        viewsList[DEFAULT_VIEW_ID]!.name = "Tools";

        const pinia = createPinia();
        const wrapper = mount(ToolPanel as object, {
            propsData: {
                workflow: false,
                editorWorkflows: null,
                dataManagers: null,
                moduleSections: null,
                useSearchWorker: false,
            },
            localVue,
            stubs: {
                icon: { template: "<div></div>" },
                ToolBox: true,
            },
            pinia,
        });

        await flushPromises();

        return wrapper;
    }

    it("test navigation of tool panel views menu", async () => {
        const wrapper = await createWrapper();
        // there is a panel view selector initially collapsed
        expect(wrapper.find(".panel-view-selector").exists()).toBeTruthy();

        // Test: starts up with a default panel view, click to open menu
        expect(wrapper.find("#toolbox-heading").text()).toBe(viewsList[DEFAULT_VIEW_ID]!.name);
        await wrapper.find("#toolbox-heading").trigger("click");
        await flushPromises();

        const dropdownMenu = wrapper.find(".dropdown-menu");
        expect(dropdownMenu.exists()).toBeTruthy();

        // Test: check if the dropdown menu has all the panel views
        const dropdownItems = dropdownMenu.findAll(".dropdown-item");
        expect(dropdownItems.length).toEqual(Object.keys(viewsList).length);

        // Test: click on each panel view, and check if the panel view is changed
        for (const [key, value] of Object.entries(viewsList)) {
            // find dropdown item
            const currItem = dropdownMenu.find(`[data-panel-id='${key}']`);
            if (key !== DEFAULT_VIEW_ID) {
                // Test: check if the panel view has appropriate description
                const description = currItem.attributes().title || null;
                expect(description).toBe(value.description);

                // set current panel view
                await currItem.trigger("click");
                await flushPromises();

                // Test: check if the current panel view is selected now
                expect(currItem.find(".fa-check").exists()).toBe(true);

                // Test: check if the panel header now has an icon and a changed name
                const panelViewIcon = wrapper.find("[data-description='panel view header icon']");
                expect(panelViewIcon.classes()).toContain(
                    `fa-${types_to_icons[value.view_type as keyof typeof types_to_icons]}`
                );
                expect(wrapper.find("#toolbox-heading").text()).toBe(value!.name);
            } else {
                // Test: check if the default panel view is already selected, and no icon
                expect(currItem.find(".fa-check").exists()).toBe(true);
                expect(wrapper.find("[data-description='panel view header icon']").exists()).toBe(false);
            }
        }
    });

    it("initializes non default current panel view correctly", async () => {
        const { viewKey, view } = storeNonDefaultView();
        const wrapper = await createWrapper();
        expect(wrapper.find(".alert").exists()).toBeFalsy();
        expect(wrapper.find("#toolbox-heading").text()).toBe(view!.name);
        const toolStore = useToolStore();
        expect(toolStore.currentPanelView).toBe(viewKey);
    });

    it("changes panel to default if current panel view throws error", async () => {
        const { viewKey, view } = storeNonDefaultView();
        const wrapper = await createWrapper(viewKey);
        expect(wrapper.find("#toolbox-heading").text()).not.toBe(view!.name);
        expect(wrapper.find("#toolbox-heading").text()).toBe(viewsList[DEFAULT_VIEW_ID]!.name);
        const toolStore = useToolStore();
        expect(toolStore.currentPanelView).toBe(DEFAULT_VIEW_ID);
        expect(wrapper.find('[data-description="panel toolbox"]').exists()).toBe(true);
    });

    it("simply shows error if even default panel view throws error", async () => {
        const { viewKey } = storeNonDefaultView();
        const wrapper = await createWrapper(viewKey, true);
        expect(wrapper.find('[data-description="panel toolbox"]').exists()).toBeFalsy();
        expect(wrapper.find('[data-description="tool panel error message"]').text()).toBe(PANEL_VIEW_ERR_MSG);
    });
});

describe("ToolPanel - Create/Edit Tool Modals", () => {
    /**
     * Creates a ToolPanel wrapper with ToolBox NOT stubbed so we can test the full integration
     */
    async function createWrapperWithToolBox(axiosMock?: MockAdapter) {
        if (!axiosMock) {
            axiosMock = new MockAdapter(axios);
        }

        axiosMock
            .onGet(`/api/tools?in_panel=False`)
            .replyOnce(200, toolsList)
            .onGet(TEST_PANELS_URI)
            .reply(200, { default_panel_view: DEFAULT_VIEW_ID, views: viewsListJson });

        axiosMock.onGet(/\/api\/tool_panels\/.*/).reply(200, toolsListInPanel);

        server.use(
            http.get("/api/users/{user_id}", ({ response }) => {
                return response(200).json(getFakeRegisteredUser());
            })
        );

        const pinia = createPinia();
        const wrapper = mount(ToolPanel as object, {
            propsData: {
                workflow: false,
                editorWorkflows: null,
                dataManagers: null,
                moduleSections: null,
                useSearchWorker: false,
            },
            localVue,
            stubs: {
                icon: { template: "<div></div>" },
                // DON'T stub ToolBox so we can test the full integration
            },
            pinia,
        });

        await flushPromises();
        return { wrapper, axiosMock };
    }

    it("should show create modal when create tool button is clicked", async () => {
        const { wrapper } = await createWrapperWithToolBox();

        // Find and click the create tool button in ToolBox
        const toolBox = wrapper.findComponent({ name: "ToolBox" });
        expect(toolBox.exists()).toBe(true);

        const createButton = toolBox.find("#create-tool-button");
        expect(createButton.exists()).toBe(true);

        await createButton.trigger("click");
        await wrapper.vm.$nextTick();

        // Modal should now be visible
        const modal = wrapper.find("#create-tool-modal");
        expect(modal.exists()).toBe(true);
        expect(modal.isVisible()).toBe(true);
    });

    it("should show success message and keep modal open after successful tool creation", async () => {
        const axiosMock = new MockAdapter(axios);
        axiosMock.onPost("/api/tools/create_tool_config/").reply(200, { id: "new_tool" });
        axiosMock.onGet(/api\/tools/).reply(200, toolsList);
        axiosMock.onGet(`/api/tools?in_panel=False`).reply(200, [...toolsList, { id: "new_tool", name: "test_tool" }]);
        axiosMock.onGet(TEST_PANELS_URI).reply(200, { default_panel_view: DEFAULT_VIEW_ID, views: viewsListJson });
        axiosMock.onGet(/\/api\/tool_panels\/.*/).reply(200, toolsListInPanel);

        const { wrapper } = await createWrapperWithToolBox(axiosMock);

        // Click create tool button to open modal
        const toolBox = wrapper.findComponent({ name: "ToolBox" });
        const createButton = toolBox.find("#create-tool-button");
        await createButton.trigger("click");
        await wrapper.vm.$nextTick();

        // Enter tool name in the modal input
        const input = wrapper.find("input[placeholder='Enter tool name']");
        await input.setValue("test_tool");
        await wrapper.vm.$nextTick();

        // Click create button
        const confirmButton = wrapper.find("#create-tool-modal .modal-footer .btn-primary");
        await confirmButton.trigger("click");
        await flushPromises();

        // Assert modal still contains success message
        const successAlert = wrapper.find("#create-tool-modal .alert-success");
        expect(successAlert.exists()).toBe(true);
        expect(successAlert.text()).toContain("Tool created successfully");

        // Assert modal element is visible in DOM
        const modal = wrapper.find("#create-tool-modal");
        expect(modal.exists()).toBe(true);
    });

    it("should display error and keep modal open on failed tool creation", async () => {
        const axiosMock = new MockAdapter(axios);
        axiosMock.onPost("/api/tools/create_tool_config/").reply(403, { message: "Permission denied" });
        axiosMock.onGet(`/api/tools?in_panel=False`).reply(200, toolsList);
        axiosMock.onGet(TEST_PANELS_URI).reply(200, { default_panel_view: DEFAULT_VIEW_ID, views: viewsListJson });
        axiosMock.onGet(/\/api\/tool_panels\/.*/).reply(200, toolsListInPanel);

        const { wrapper } = await createWrapperWithToolBox(axiosMock);

        // Click create tool button to open modal
        const toolBox = wrapper.findComponent({ name: "ToolBox" });
        const createButton = toolBox.find("#create-tool-button");
        await createButton.trigger("click");
        await wrapper.vm.$nextTick();

        // Enter tool name in the modal input
        const input = wrapper.find("input[placeholder='Enter tool name']");
        await input.setValue("test_tool");
        await wrapper.vm.$nextTick();

        // Click create button
        const confirmButton = wrapper.find("#create-tool-modal .modal-footer .btn-primary");
        await confirmButton.trigger("click");
        await flushPromises();

        // Assert error is displayed and modal stays open
        const errorAlert = wrapper.find("#create-tool-modal .alert-danger");
        expect(errorAlert.exists()).toBe(true);
        expect(errorAlert.text()).toContain("Permission denied");

        // Modal should still be visible
        const modal = wrapper.find("#create-tool-modal");
        expect(modal.exists()).toBe(true);
    });

    it("should show edit modal when edit is triggered", async () => {
        const { wrapper } = await createWrapperWithToolBox();

        // Find the ToolBox component and trigger edit
        const toolBox = wrapper.findComponent({ name: "ToolBox" });
        expect(toolBox.exists()).toBe(true);

        // Emit the onEditTool event from ToolBox
        toolBox.vm.$emit("onEditTool", "tool_id_123", "Original Tool Name");
        await wrapper.vm.$nextTick();

        // Modal should be visible
        const modal = wrapper.find("#edit-tool-modal");
        expect(modal.exists()).toBe(true);
        expect(modal.isVisible()).toBe(true);
    });

    it("should keep modal open after successful tool edit", async () => {
        const axiosMock = new MockAdapter(axios);
        axiosMock.onPost("/api/tools/edit_tool_config/").reply(200);
        axiosMock.onGet(/api\/tools/).reply(200, toolsList);
        axiosMock.onGet(`/api/tools?in_panel=False`).reply(200, toolsList);
        axiosMock.onGet(TEST_PANELS_URI).reply(200, { default_panel_view: DEFAULT_VIEW_ID, views: viewsListJson });
        axiosMock.onGet(/\/api\/tool_panels\/.*/).reply(200, toolsListInPanel);

        const { wrapper } = await createWrapperWithToolBox(axiosMock);

        // Find the ToolBox component and trigger edit
        const toolBox = wrapper.findComponent({ name: "ToolBox" });
        toolBox.vm.$emit("onEditTool", "tool_123", "Updated Tool Name");
        await wrapper.vm.$nextTick();

        // Enter new tool name in the modal input
        const input = wrapper.find("#edit-tool-modal input[placeholder='Enter tool name']");
        await input.setValue("Updated Tool Name");
        await wrapper.vm.$nextTick();

        // Click save button
        const saveButton = wrapper.find("#edit-tool-modal .modal-footer .btn-primary");
        await saveButton.trigger("click");
        await flushPromises();

        // Assert modal still contains success message
        const successAlert = wrapper.find("#edit-tool-modal .alert-success");
        expect(successAlert.exists()).toBe(true);
        expect(successAlert.text()).toContain("Tool updated successfully");

        // Modal should still be open
        const modal = wrapper.find("#edit-tool-modal");
        expect(modal.exists()).toBe(true);
    });

    it("should persist modal state across ToolBox re-renders", async () => {
        const axiosMock = new MockAdapter(axios);
        axiosMock.onPost("/api/tools/create_tool_config/").reply(200, { id: "new_tool" });
        axiosMock.onGet(/api\/tools/).reply(200, toolsList);
        axiosMock
            .onGet(`/api/tools?in_panel=False`)
            .replyOnce(200, toolsList)
            .onGet(`/api/tools?in_panel=False`)
            .replyOnce(200, [...toolsList, { id: "new_tool", name: "test_tool" }]);
        axiosMock.onGet(TEST_PANELS_URI).reply(200, { default_panel_view: DEFAULT_VIEW_ID, views: viewsListJson });
        axiosMock.onGet(/\/api\/tool_panels\/.*/).reply(200, toolsListInPanel);

        const { wrapper } = await createWrapperWithToolBox(axiosMock);

        // Click create tool button to open modal
        const toolBox = wrapper.findComponent({ name: "ToolBox" });
        const createButton = toolBox.find("#create-tool-button");
        await createButton.trigger("click");
        await wrapper.vm.$nextTick();

        // Enter tool name
        const input = wrapper.find("input[placeholder='Enter tool name']");
        await input.setValue("test_tool");
        await wrapper.vm.$nextTick();

        // Click create button
        const confirmButton = wrapper.find("#create-tool-modal .modal-footer .btn-primary");
        await confirmButton.trigger("click");
        await flushPromises();

        // Modal should still be open with success message
        const successAlert = wrapper.find("#create-tool-modal .alert-success");
        expect(successAlert.exists()).toBe(true);

        // Even after tool refresh, modal should still be open
        const modal = wrapper.find("#create-tool-modal");
        expect(modal.exists()).toBe(true);
        expect(modal.isVisible()).toBe(true);
    });
});
