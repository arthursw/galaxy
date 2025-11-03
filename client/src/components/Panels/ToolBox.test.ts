import { mount } from "@vue/test-utils";
import { createPinia } from "pinia";
import { getLocalVue } from "tests/jest/helpers";

import ToolBox from "./ToolBox.vue";

const localVue = getLocalVue();

describe("ToolBox.vue - Event Emission", () => {
    let wrapper: any;

    beforeEach(() => {
        const pinia = createPinia();
        wrapper = mount(ToolBox, {
            propsData: {
                workflow: false,
                showAdvanced: false,
                panelQuery: "",
            },
            localVue,
            stubs: {
                ToolSearch: true,
                ToolSection: {
                    template: `
                        <div>
                            <button @click="$emit('onEditTool', 'test_tool', 'Test Tool')">Edit</button>
                            <button @click="$emit('onDeleteTool', 'test_tool')">Delete</button>
                            <button @click="$emit('onOpenTool', 'test_tool')">Open</button>
                        </div>
                    `,
                    props: ["category", "queryFilter", "disableFilter", "showToolActions"],
                    emits: ["onClick", "onFilter", "onEditTool", "onDeleteTool", "onOpenTool"],
                },
                BButton: { template: "<button @click=\"$listeners.click\"><slot /></button>" },
            },
            pinia,
        });
    });

    describe("Event Emission Tests", () => {
        it("should emit onCreateTool event when create button is clicked", async () => {
            const createButton = wrapper.find("#create-tool-button");
            await createButton.trigger("click");

            expect(wrapper.emitted("onCreateTool")).toBeTruthy();
        });

        it("should emit onEditTool event with tool id and name when edit is triggered", async () => {
            const toolSection = wrapper.findComponent({ name: "ToolSection" });
            // Simulate the ToolSection emitting onEditTool
            toolSection.vm.$emit("onEditTool", "tool_123", "Tool Name");

            // Check if ToolBox re-emits it
            expect(wrapper.emitted("onEditTool")).toBeTruthy();
            expect(wrapper.emitted("onEditTool")[0]).toEqual(["tool_123", "Tool Name"]);
        });

        it("should emit onDeleteTool event with tool id when delete is triggered", async () => {
            const toolSection = wrapper.findComponent({ name: "ToolSection" });
            toolSection.vm.$emit("onDeleteTool", "tool_456");

            expect(wrapper.emitted("onDeleteTool")).toBeTruthy();
            expect(wrapper.emitted("onDeleteTool")[0]).toEqual(["tool_456"]);
        });

        it("should emit onOpenTool event with tool id when open is triggered", async () => {
            const toolSection = wrapper.findComponent({ name: "ToolSection" });
            toolSection.vm.$emit("onOpenTool", "tool_789");

            expect(wrapper.emitted("onOpenTool")).toBeTruthy();
            expect(wrapper.emitted("onOpenTool")[0]).toEqual(["tool_789"]);
        });
    });
});
