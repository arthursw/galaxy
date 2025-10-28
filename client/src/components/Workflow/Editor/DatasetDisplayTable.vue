<template>
  <div v-if="activeStepId" class="dataset-table">
    <div class="bg-secondary px-2 py-1 rounded d-flex flex-gapx-1 justify-content-between">
      <b>Outputs for Step: {{ activeStepId }}</b>
    </div>

    <div v-if="loading">Loading datasets...</div>
    <div v-if="error" class="error">{{ error }}</div>

    <table v-if="datasets.length > 0" class="outputs-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Extension</th>
          <th>Preview</th>
          <th>Download</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="dataset in datasets" :key="dataset.id">
          <td>{{ dataset.name }}</td>
          <td>{{ dataset.extension }}</td>
          <td>
            <img
              v-if="isImage(dataset.extension)"
              :src="getThumbnailUrl(dataset)"
              alt="Preview"
              style="width: 80px; height: auto; border: 1px solid #ccc;"
            />
            <!-- <button
              v-else-if="dataset.data_type.includes('tabular')"
              @click="openPreview(dataset)"
            >
              Preview
            </button> -->
            <iframe
              v-else-if="dataset.data_type && dataset.data_type.includes('tabular')"
              title="uid"
              :src="`/datasets/${dataset.id}/display/?preview=True`"
              width="600"
              height="400"
              style="border: none;"
            ></iframe>
            <span v-else>-</span>
          </td>
          <td>
            <a
              :href="`${galaxyBaseUrl}${dataset.download_url}`"
              target="_blank"
            >
              Download
            </a>

            <button v-if="isImage(dataset.extension)" @click="openInNapari(dataset.id)">Open in Napari</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- Modal for tabular preview -->
    <!-- <div v-if="previewDataset" class="modal">
      <div class="modal-content">
        <h4>{{ previewDataset.name }} Preview</h4>
        <iframe
          title="uid"
          :src="`/datasets/${previewDataset.id}/display/?preview=True`"
          width="600"
          height="400"
          style="border: none;"
        ></iframe>
        <button @click="closePreview">Close</button>
      </div>
    </div> -->
  </div>
</template>

<script lang="ts">
import axios from "axios";
import type { StrokeCap } from "vega";
import type { PropType } from "vue";
import { defineComponent } from "vue";

interface Dataset {
  id: number | string;
  name: string;
  extension: string;
  download_url: string;
  data_type: string;
}

export default defineComponent({
  name: "WorkflowStepDatasetsViewer",
  props: {
    workflowId: {
      type: String as PropType<string>,
      required: true,
    },
    activeStepId: {
      type: Number as PropType<number | null>,
      default: null,
    },
    galaxyBaseUrl: {
      type: String as PropType<string>,
      default: "",
    },
  },
  data() {
    return {
      loading: false as boolean,
      error: null as string | null,
      datasets: [] as Dataset[],
      // previewDataset: null as Dataset | null,
    };
  },
  watch: {
    activeStepId(newVal: number | null, oldVal: number | null) {
      if (newVal != null && newVal !== oldVal) {
        this.fetchDatasets();
      }
    },
  },
  mounted() {
    this.fetchDatasets();
  },
  methods: {
    async fetchDatasets(): Promise<void> {
      try {
        this.loading = true;
        this.error = null;

        // 1. Get last invocation
        const invocationsRes = await axios.get<any>(
          `${this.galaxyBaseUrl}/api/invocations`,
          {
            params: {
              limit: 1,
              sort_by: "create_time",
              sort_desc: true,
              workflow_id: this.workflowId,
            },
          }
        );
        const invocationsArray = Object.values(invocationsRes.data);
        const lastInvocation = invocationsArray[0] as any;
        if (!lastInvocation) {
          throw new Error("No invocations found.");
        }

        // 2. Invocation details
        const invocationRes = await axios.get<any>(
          `${this.galaxyBaseUrl}/api/invocations/${lastInvocation.id}`
        );
        const steps = invocationRes.data.steps || [];
        const step = steps.find((s: any) => s.order_index === this.activeStepId);
        if (!step) {
          throw new Error("Step not found in invocation.");
        }

        // 3. Step details
        const stepDetailRes = await axios.get<any>(
          `${this.galaxyBaseUrl}/api/invocations/steps/${step.id}`
        );

        // 3. Get all jobs for this step
        const jobs = stepDetailRes.data.jobs || [];
        if (!jobs.length) {
          throw new Error("No jobs for this step.");
        }

        // 4. Fetch all job details in parallel
        const jobDetailsPromises = jobs.map((job: any) =>
          axios.get<any>(`${this.galaxyBaseUrl}/api/jobs/${job.id}`, { params: { full: true } })
        );
        const jobDetailsResponses = await Promise.all(jobDetailsPromises);

        // 5. Collect all dataset IDs from all jobs
        const datasetIds = jobDetailsResponses.flatMap((jobRes: any) =>
          Object.values(jobRes.data.outputs || {}).map((o: any) => o.id)
        );

        // (Optional) Expand collections into datasets later if needed
        // For now, just ignore collections

        // 6. Fetch all datasets in parallel
        const datasetPromises = datasetIds.map((id: number | string) =>
          axios.get<any>(`${this.galaxyBaseUrl}/api/datasets/${id}`)
        );
        const datasetResponses = await Promise.all(datasetPromises);

        // Map responses to dataset objects
        const tempDatasets = datasetResponses
          .map((res: any) => res.data)
          .filter((d: any) => d && typeof d.id !== "undefined") as Dataset[];

        // For image datasets, ask the server to generate thumbnails if necessary.
        // We don't fail the whole flow if thumbnail generation fails for a dataset.
        const generatePromises = tempDatasets.map((d: Dataset) => {
          if (this.isImage(d.extension)) {
            // Trigger thumbnail generation (server will skip if not needed)
            return axios
              .put(`${this.galaxyBaseUrl}/api/datasets/${d.id}/thumbnail/`)
              .catch(() => null);
          }
          return Promise.resolve(null);
        });
        await Promise.all(generatePromises);
        this.datasets = tempDatasets;
      } catch (err) {
        if (err instanceof Error) {
          this.error = err.message;
        } else {
          this.error = String(err);
        }
        this.datasets = [];
        console.warn(err);
      } finally {
        this.loading = false;
      }
    },
    getThumbnailUrl(dataset: Dataset): string {
      return `${this.galaxyBaseUrl}/api/datasets/${dataset.id}/thumbnail/`;
    },
    isImage(ext?: string | null): boolean {
      if (!ext) {
        return false;
      }
      return ["png", "jpg", "jpeg", "gif", "tif", "tiff", "ome.tiff", "zar"].includes(ext.toLowerCase());
    },
    // openPreview(dataset: Dataset) {
    //   this.previewDataset = dataset;
    // },
    // closePreview() {
    //   this.previewDataset = null;
    // },
    openInNapari(dataset_id: string | number) {
      axios.get(`${this.galaxyBaseUrl}/api/datasets/${dataset_id}/open_image/`).catch(() => null);
    },
  },
});
</script>

<style scoped>
.outputs-table {
  border-collapse: collapse;
  width: 100%;
  margin-top: 10px;
}
.outputs-table th,
.outputs-table td {
  border: 1px solid #ddd;
  padding: 8px;
}
.outputs-table th {
  background-color: #f2f2f2;
  text-align: left;
}
.modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
}
.modal-content {
  background: white;
  padding: 20px;
  margin: 50px auto;
  max-width: 700px;
  border-radius: 6px;
}
</style>
