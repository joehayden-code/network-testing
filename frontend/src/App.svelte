<script>
  import { uploadConfig } from "./lib/api.js";
  import Sidebar from "./components/Sidebar.svelte";
  import RunPanel from "./components/RunPanel.svelte";
  import DiffPanel from "./components/DiffPanel.svelte";

  // null = no file loaded yet; object = parsed config from uploaded YAML
  let config = $state(null);
  let view = $state("run");
  let uploading = $state(false);
  let uploadError = $state(null);
  let fileName = $state(null);

  // Shared hidden file input so both the landing page and the sidebar
  // "Change File" button can trigger the same upload handler.
  let fileInput = $state(null);

  function openFilePicker() {
    fileInput?.click();
  }

  async function handleFileInput(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    await doUpload(file);
    // Reset so re-selecting the same file still fires onchange
    e.target.value = "";
  }

  async function doUpload(file) {
    uploading = true;
    uploadError = null;
    try {
      config = await uploadConfig(file);
      fileName = file.name;
    } catch (e) {
      uploadError = e.message;
    } finally {
      uploading = false;
    }
  }

  // Drag-and-drop on the landing page
  let dragging = $state(false);

  function onDragOver(e) {
    e.preventDefault();
    dragging = true;
  }

  function onDragLeave() {
    dragging = false;
  }

  function onDrop(e) {
    e.preventDefault();
    dragging = false;
    const file = e.dataTransfer?.files?.[0];
    if (file) doUpload(file);
  }
</script>

<!-- Hidden file input shared across the page -->
<input
  bind:this={fileInput}
  type="file"
  accept=".yaml,.yml"
  class="hidden"
  onchange={handleFileInput}
/>

<div class="flex h-screen overflow-hidden bg-slate-900 text-slate-100">
  {#if !config}
    <!-- ── Upload landing ── -->
    <div class="flex flex-1 flex-col items-center justify-center px-6">
      <div class="mb-8 text-center">
        <div class="mb-2 flex items-center justify-center gap-2">
          <span class="inline-block h-2.5 w-2.5 rounded-full bg-cyan-400"></span>
          <h1 class="text-xl font-semibold uppercase tracking-widest text-slate-100">
            Network Testing
          </h1>
        </div>
        <p class="text-sm text-slate-500">Pre / Post Change Validation</p>
      </div>

      <!-- Drop zone -->
      <button
        onclick={openFilePicker}
        ondragover={onDragOver}
        ondragleave={onDragLeave}
        ondrop={onDrop}
        class="relative flex w-full max-w-md cursor-pointer flex-col items-center gap-4 rounded-xl border-2 border-dashed px-10 py-14 text-center transition-colors
          {dragging
          ? 'border-cyan-400 bg-cyan-950/20'
          : 'border-slate-600 bg-slate-800/50 hover:border-slate-500 hover:bg-slate-800'}"
      >
        {#if uploading}
          <div class="h-10 w-10 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent"></div>
          <p class="text-sm text-slate-300">Parsing YAML…</p>
        {:else}
          <!-- YAML file icon -->
          <svg
            class="h-12 w-12 text-slate-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>

          <div>
            <p class="mb-1 font-medium text-slate-200">
              Drop your YAML file here
            </p>
            <p class="text-sm text-slate-500">
              or <span class="text-cyan-400 underline underline-offset-2">click to browse</span>
            </p>
            <p class="mt-3 text-xs text-slate-600">
              Accepts <code class="font-mono">.yaml</code> / <code class="font-mono">.yml</code>
            </p>
          </div>
        {/if}
      </button>

      {#if uploadError}
        <div class="mt-4 flex items-start gap-2 rounded-lg bg-red-950/60 px-4 py-3 text-sm text-red-300 max-w-md w-full">
          <span class="flex-shrink-0">⚠</span>
          <span>{uploadError}</span>
        </div>
      {/if}

      <p class="mt-8 max-w-sm text-center text-xs text-slate-600 leading-relaxed">
        Credentials are read from <code class="font-mono text-slate-500">NET_USERNAME</code>,
        <code class="font-mono text-slate-500">NET_PASSWORD</code>, and
        <code class="font-mono text-slate-500">NET_SECRET</code> environment variables set on the server.
      </p>
    </div>
  {:else}
    <!-- ── Main app ── -->
    <Sidebar {config} bind:view {fileName} onChangeFile={openFilePicker} />
    <main class="flex min-w-0 flex-1 flex-col overflow-hidden">
      {#if view === "run"}
        <RunPanel {config} />
      {:else if view === "diff"}
        <DiffPanel />
      {/if}
    </main>
  {/if}
</div>
