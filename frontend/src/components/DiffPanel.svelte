<script>
  import { onMount } from "svelte";
  import { getDiff } from "../lib/api.js";

  let loading = $state(false);
  let error = $state(null);
  let diffData = $state(null);
  let selected = $state(null);
  let viewMode = $state("unified"); // 'unified' | 'split'
  let changedOnly = $state(false);
  let copiedDiff = $state(false);

  onMount(loadDiff);

  async function loadDiff() {
    loading = true;
    error = null;
    try {
      diffData = await getDiff();
      selected = null;
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  let visibleDiffs = $derived(
    diffData?.diffs?.filter((d) => !changedOnly || d.changed) ?? []
  );

  let changedCount = $derived(diffData?.diffs?.filter((d) => d.changed).length ?? 0);

  function fmtTime(ts) {
    if (!ts) return "—";
    return new Date(ts).toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }

  /** Parse a unified diff string into annotated lines for display */
  function parseDiff(raw) {
    if (!raw) return [];
    return raw.split("\n").map((line) => {
      if (line.startsWith("+++") || line.startsWith("---"))
        return { text: line, cls: "text-slate-500" };
      if (line.startsWith("@@"))
        return { text: line, cls: "text-cyan-600 bg-cyan-950/30" };
      if (line.startsWith("+"))
        return { text: line, cls: "text-emerald-400 bg-emerald-950/40" };
      if (line.startsWith("-"))
        return { text: line, cls: "text-red-400 bg-red-950/40" };
      return { text: line, cls: "text-slate-300" };
    });
  }

  async function copySelected() {
    if (!selected) return;
    const text = selected.diff
      ? selected.diff
      : `PRE:\n${selected.pre}\n\nPOST:\n${selected.post}`;
    try {
      await navigator.clipboard.writeText(text);
      copiedDiff = true;
      setTimeout(() => (copiedDiff = false), 2000);
    } catch {
      /* ignore */
    }
  }
</script>

<div class="flex h-full flex-col overflow-hidden">
  <!-- Header -->
  <div class="flex-shrink-0 border-b border-slate-700 bg-slate-800 px-4 py-3">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div>
        <h2 class="font-semibold text-slate-100">Pre / Post Diff</h2>
        {#if diffData}
          <p class="mt-0.5 text-xs text-slate-500">
            <span class="text-blue-400">Pre:</span>
            {fmtTime(diffData.pre_timestamp)}
            <span class="mx-2 text-slate-700">→</span>
            <span class="text-purple-400">Post:</span>
            {fmtTime(diffData.post_timestamp)}
          </p>
        {/if}
      </div>

      <div class="flex items-center gap-2">
        {#if diffData}
          <label class="flex cursor-pointer items-center gap-1.5 text-xs text-slate-400">
            <input
              type="checkbox"
              bind:checked={changedOnly}
              class="h-3.5 w-3.5 accent-cyan-500"
            />
            Changed only
          </label>
          <div class="flex overflow-hidden rounded border border-slate-700">
            {#each ["unified", "split"] as v}
              <button
                onclick={() => (viewMode = v)}
                class="px-2 py-1 text-xs capitalize transition-colors
                  {viewMode === v
                  ? 'bg-slate-600 text-slate-100'
                  : 'bg-slate-800 text-slate-400 hover:bg-slate-700'}"
              >
                {v}
              </button>
            {/each}
          </div>
        {/if}
        <button
          onclick={loadDiff}
          class="rounded px-3 py-1.5 text-xs text-slate-300 bg-slate-700 hover:bg-slate-600 transition-colors"
        >
          Refresh
        </button>
      </div>
    </div>
  </div>

  <!-- Body -->
  {#if loading}
    <div class="flex flex-1 items-center justify-center">
      <div class="text-center">
        <div
          class="mb-3 inline-block h-6 w-6 animate-spin rounded-full border-2 border-cyan-400 border-t-transparent"
        ></div>
        <p class="text-sm text-slate-400">Loading diff…</p>
      </div>
    </div>

  {:else if error}
    <div class="flex flex-1 items-center justify-center">
      <div class="max-w-sm text-center">
        <div class="mb-3 text-3xl text-amber-400">⚠</div>
        <p class="mb-1 text-slate-300">{error}</p>
        <p class="text-sm text-slate-500">
          Run a Pre-Check and a Post-Check first, then come back here.
        </p>
      </div>
    </div>

  {:else if diffData}
    <div class="flex min-h-0 flex-1">
      <!-- Test list sidebar -->
      <div
        class="w-64 flex-shrink-0 overflow-y-auto border-r border-slate-700 bg-slate-800"
      >
        <div class="p-2">
          <p class="mb-1 px-2 text-xs text-slate-500">
            {changedCount} changed / {diffData.diffs?.length ?? 0} total
          </p>

          {#each visibleDiffs as d}
            <button
              onclick={() => (selected = d)}
              class="mb-0.5 w-full rounded px-2 py-2 text-left text-sm transition-colors
                {selected === d ? 'bg-slate-700' : 'hover:bg-slate-700/40'}"
            >
              <div class="mb-0.5 flex items-center gap-1.5">
                <span
                  class="inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full
                    {d.changed ? 'bg-amber-400' : 'bg-emerald-500'}"
                ></span>
                <span class="truncate text-xs font-semibold text-cyan-400">
                  {d.device}
                </span>
              </div>
              <p class="truncate pl-3 text-xs text-slate-400">{d.test}</p>
              <p class="pl-3 text-xs {d.changed ? 'text-amber-500' : 'text-emerald-600'}">
                {d.changed ? "Modified" : "Unchanged"}
              </p>
            </button>
          {/each}

          {#if visibleDiffs.length === 0}
            <p class="px-2 text-xs italic text-slate-600">No results</p>
          {/if}
        </div>
      </div>

      <!-- Diff content pane -->
      <div class="flex min-w-0 flex-1 flex-col overflow-hidden">
        {#if selected}
          <!-- Pane header -->
          <div
            class="flex flex-shrink-0 items-center justify-between border-b border-slate-700 bg-slate-800/60 px-4 py-2"
          >
            <div class="text-sm">
              <span class="font-semibold text-cyan-400">{selected.device}</span>
              <span class="mx-1 text-slate-600">›</span>
              <span class="text-slate-200">{selected.test}</span>
              {#if !selected.changed}
                <span class="ml-2 text-xs text-emerald-500">(no changes)</span>
              {/if}
            </div>
            <button
              onclick={copySelected}
              class="flex items-center gap-1.5 rounded px-2 py-1 text-xs transition-colors
                {copiedDiff
                ? 'bg-emerald-800/60 text-emerald-300'
                : 'bg-slate-700 text-slate-400 hover:bg-slate-600 hover:text-slate-200'}"
            >
              {#if copiedDiff}
                ✓ Copied!
              {:else}
                <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
                Copy
              {/if}
            </button>
          </div>

          <!-- Diff body -->
          <div class="min-h-0 flex-1 overflow-hidden">
            {#if viewMode === "unified"}
              <div class="console-font h-full overflow-y-auto p-4">
                {#if selected.diff}
                  {#each parseDiff(selected.diff) as line}
                    <div class="whitespace-pre-wrap break-words {line.cls}">{line.text}</div>
                  {/each}
                {:else}
                  <p class="italic text-slate-600">No differences detected.</p>
                {/if}
              </div>
            {:else}
              <!-- Split view -->
              <div class="grid h-full grid-cols-2 divide-x divide-slate-700 overflow-hidden">
                <div class="console-font overflow-y-auto p-4">
                  <p class="mb-2 text-xs font-semibold text-blue-400">PRE</p>
                  <pre class="whitespace-pre-wrap break-words text-slate-300">{selected.pre || "(empty)"}</pre>
                </div>
                <div class="console-font overflow-y-auto p-4">
                  <p class="mb-2 text-xs font-semibold text-purple-400">POST</p>
                  <pre class="whitespace-pre-wrap break-words text-slate-300">{selected.post || "(empty)"}</pre>
                </div>
              </div>
            {/if}
          </div>
        {:else}
          <div class="flex flex-1 items-center justify-center text-slate-700">
            <div class="text-center">
              <div class="mb-2 text-3xl">←</div>
              <p class="text-sm">Select a test result to view its diff</p>
            </div>
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>
