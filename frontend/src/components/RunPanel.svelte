<script>
  import { onMount } from "svelte";
  import { runTests, getSnapshots, deleteSnapshot } from "../lib/api.js";
  import ConsoleOutput from "./ConsoleOutput.svelte";

  let { config } = $props();

  let mode = $state("immediate"); // 'pre' | 'immediate' | 'post'
  let running = $state(false);
  let events = $state([]);
  let snapshots = $state({ pre: { exists: false }, post: { exists: false } });

  let enabledTests = $derived(config.tests?.filter((t) => t.enabled) ?? []);
  let deviceCount = $derived(config.inventory?.length ?? 0);
  let canRun = $derived(!running && enabledTests.length > 0 && deviceCount > 0);

  onMount(refreshSnapshots);

  async function refreshSnapshots() {
    try {
      snapshots = await getSnapshots();
    } catch {
      /* non-fatal */
    }
  }

  async function handleRun() {
    if (!canRun) return;
    running = true;
    events = [];
    try {
      for await (const event of runTests(mode, config)) {
        events = [...events, event];
      }
    } catch (e) {
      events = [...events, { type: "error", message: e.message }];
    } finally {
      running = false;
      await refreshSnapshots();
    }
  }

  async function handleDeleteSnapshot(m) {
    try {
      await deleteSnapshot(m);
      await refreshSnapshots();
    } catch {
      /* ignore */
    }
  }

  function fmtTime(ts) {
    if (!ts) return null;
    return new Date(ts).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  const modeConfig = [
    { value: "pre", label: "Pre-Check", activeClass: "bg-blue-600 text-white" },
    { value: "immediate", label: "Run Now", activeClass: "bg-emerald-600 text-white" },
    { value: "post", label: "Post-Check", activeClass: "bg-purple-600 text-white" },
  ];
</script>

<div class="flex h-full flex-col overflow-hidden">
  <!-- Control bar -->
  <div class="flex-shrink-0 border-b border-slate-700 bg-slate-800 px-4 py-3">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <!-- Mode buttons -->
      <div class="flex items-center gap-2">
        <span class="text-xs text-slate-500">Mode:</span>
        <div class="flex overflow-hidden rounded-lg border border-slate-700">
          {#each modeConfig as m}
            <button
              onclick={() => (mode = m.value)}
              class="px-3 py-1.5 text-sm font-medium transition-colors
                {mode === m.value
                ? m.activeClass
                : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'}"
            >
              {m.label}
            </button>
          {/each}
        </div>
      </div>

      <!-- Stats + Execute -->
      <div class="flex items-center gap-4">
        <span class="text-xs text-slate-500">
          <span class="text-slate-200">{deviceCount}</span>
          {deviceCount === 1 ? "device" : "devices"} &middot;
          <span class="text-slate-200">{enabledTests.length}</span>
          {enabledTests.length === 1 ? "test" : "tests"} enabled
        </span>

        <button
          onclick={handleRun}
          disabled={!canRun}
          class="flex items-center gap-2 rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium
                 text-white transition-colors hover:bg-cyan-500
                 disabled:cursor-not-allowed disabled:opacity-40"
        >
          {#if running}
            <span
              class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white border-t-transparent"
            ></span>
            Running…
          {:else}
            <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Execute
          {/if}
        </button>
      </div>
    </div>

    <!-- Snapshot status row -->
    <div class="mt-2.5 flex flex-wrap items-center gap-5">
      {#each [{ key: "pre", label: "Pre Snapshot", dotClass: "bg-blue-400" }, { key: "post", label: "Post Snapshot", dotClass: "bg-purple-400" }] as snap}
        <div class="flex items-center gap-1.5 text-xs">
          <span
            class="inline-block h-1.5 w-1.5 rounded-full {snapshots[snap.key]?.exists
              ? snap.dotClass
              : 'bg-slate-700'}"
          ></span>
          <span class="text-slate-500">{snap.label}:</span>
          {#if snapshots[snap.key]?.exists}
            <span class="text-slate-300">{fmtTime(snapshots[snap.key].timestamp)}</span>
            <button
              onclick={() => handleDeleteSnapshot(snap.key)}
              class="ml-0.5 text-slate-600 hover:text-red-400 transition-colors"
              title="Delete snapshot"
            >✕</button>
          {:else}
            <span class="text-slate-700">None</span>
          {/if}
        </div>
      {/each}

      {#if enabledTests.length === 0}
        <span class="text-xs text-amber-500">⚠ No tests enabled — toggle some in the sidebar</span>
      {/if}
    </div>
  </div>

  <!-- Console -->
  <div class="min-h-0 flex-1 overflow-hidden">
    <ConsoleOutput {events} {running} />
  </div>
</div>
