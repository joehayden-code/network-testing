<script>
  let { config, view = $bindable("run"), fileName = null, onChangeFile } = $props();

  // Only tests marked enabled in the YAML are shown
  let enabledTests = $derived(config.tests?.filter((t) => t.enabled) ?? []);

  const navItems = [
    {
      value: "run",
      label: "Run Tests",
      icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"/>
             <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>`,
    },
    {
      value: "diff",
      label: "View Diff",
      icon: `<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/>`,
    },
  ];
</script>

<aside
  class="flex w-64 flex-shrink-0 flex-col overflow-hidden border-r border-slate-700 bg-slate-800"
>
  <!-- Header -->
  <div class="border-b border-slate-700 px-4 py-4">
    <div class="mb-0.5 flex items-center gap-2">
      <span class="inline-block h-2 w-2 rounded-full bg-cyan-400"></span>
      <h1 class="text-sm font-semibold uppercase tracking-widest text-slate-100">
        Net Testing
      </h1>
    </div>
    <p class="text-xs text-slate-500">Pre / Post Change Validation</p>
  </div>

  <!-- Navigation -->
  <div class="border-b border-slate-700 p-2">
    {#each navItems as item}
      <button
        onclick={() => (view = item.value)}
        class="mb-0.5 flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors
          {view === item.value
          ? 'bg-slate-700 text-cyan-400'
          : 'text-slate-400 hover:bg-slate-700/50 hover:text-slate-200'}"
      >
        <svg class="h-4 w-4 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          {@html item.icon}
        </svg>
        {item.label}
      </button>
    {/each}
  </div>

  <!-- Scrollable content — read-only -->
  <div class="flex-1 overflow-y-auto">
    <!-- Devices -->
    <div class="p-3">
      <h2 class="mb-2 px-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Devices ({config.inventory?.length ?? 0})
      </h2>
      {#if config.inventory?.length}
        <div class="space-y-0.5">
          {#each config.inventory as device}
            <div class="flex items-start gap-2 rounded bg-slate-900/40 px-2 py-1.5">
              <span class="mt-1.5 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-slate-600"></span>
              <div class="min-w-0">
                <p class="truncate text-sm text-slate-200">{device.name}</p>
                <p class="truncate font-mono text-xs text-slate-500">
                  {device.device_type || "cisco_ios"}
                </p>
              </div>
            </div>
          {/each}
        </div>
      {:else}
        <p class="px-1 text-xs italic text-slate-600">No devices in inventory</p>
      {/if}
    </div>

    <!-- Tests (enabled only) -->
    <div class="border-t border-slate-700/50 p-3">
      <h2 class="mb-2 px-1 text-xs font-semibold uppercase tracking-wider text-slate-500">
        Tests ({enabledTests.length} enabled)
      </h2>
      {#if enabledTests.length}
        <div class="space-y-0.5">
          {#each enabledTests as test}
            <div class="flex items-start gap-2 rounded px-2 py-1.5">
              {#if test.type === "ping"}
                <!-- ping indicator: violet dot -->
                <span class="mt-1 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-violet-500"></span>
                <div class="min-w-0">
                  <p class="truncate text-sm text-slate-200">{test.name}</p>
                  <p class="truncate font-mono text-xs text-slate-600">
                    ping &middot; {test.destinations?.length ?? 0} destination{test.destinations?.length !== 1 ? "s" : ""}
                  </p>
                  {#if test.destinations?.length}
                    <ul class="mt-0.5 space-y-px">
                      {#each test.destinations as dest}
                        <li class="truncate font-mono text-xs text-slate-500 pl-2">→ {dest}</li>
                      {/each}
                    </ul>
                  {/if}
                </div>
              {:else}
                <!-- command test indicator: cyan dot -->
                <span class="mt-1 inline-block h-1.5 w-1.5 flex-shrink-0 rounded-full bg-cyan-600"></span>
                <div class="min-w-0">
                  <p class="truncate text-sm text-slate-200">{test.name}</p>
                  <p class="truncate font-mono text-xs text-slate-600">{test.command}</p>
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {:else}
        <p class="px-1 text-xs italic text-slate-600">No tests enabled</p>
      {/if}
    </div>
  </div>

  <!-- Footer: loaded file + change button -->
  <div class="border-t border-slate-700 p-3">
    {#if fileName}
      <div class="mb-2 flex items-center gap-1.5 rounded bg-slate-900/50 px-2 py-1.5">
        <svg class="h-3.5 w-3.5 flex-shrink-0 text-slate-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
        </svg>
        <span class="truncate font-mono text-xs text-slate-400">{fileName}</span>
      </div>
    {/if}
    <button
      onclick={onChangeFile}
      class="flex w-full items-center justify-center gap-1.5 rounded-md bg-slate-700 px-3 py-2 text-sm text-slate-300 transition-colors hover:bg-slate-600 hover:text-slate-100"
    >
      <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
      </svg>
      Load New File
    </button>
  </div>
</aside>
