<script>
  import { tick } from "svelte";

  let { events = [], running = false } = $props();

  let consoleEl = $state(null);
  let copied = $state(false);

  // Auto-scroll to bottom on new output
  $effect(() => {
    void events.length;
    tick().then(() => {
      if (consoleEl) consoleEl.scrollTop = consoleEl.scrollHeight;
    });
  });

  function toPlainText() {
    return events
      .map((e) => {
        if (e.type === "start")
          return `=== Starting: ${e.total_ping_tests ?? 0} ping test(s), ${e.total_command_tests ?? 0} device test(s) across ${e.total_devices} device(s) ===\n`;
        if (e.type === "ping_section")
          return `\n── Host Pings ──\n`;
        if (e.type === "ping_test_start")
          return `\n[HOST] ${e.test} (${e.destinations?.length} destination(s), count=${e.count})\n`;
        if (e.type === "ping_result")
          return `\n$ ping ${e.destination}\n${e.output}\n`;
        if (e.type === "device_section")
          return `\n── Device Tests ──\n`;
        if (e.type === "device_start")
          return `\n[${e.device}] Connecting to ${e.host}...\n`;
        if (e.type === "test_result")
          return `\n[${e.device}] $ ${e.command}\n${e.output}\n`;
        if (e.type === "device_error")
          return `\n[${e.device}] ERROR: ${e.message}\n`;
        if (e.type === "device_complete")
          return `[${e.device}] Session closed\n`;
        if (e.type === "complete")
          return `\n=== ${e.saved ? `Saved as ${e.mode} snapshot` : "Complete"} ===\n`;
        if (e.type === "error") return `\nERROR: ${e.message}\n`;
        return "";
      })
      .join("");
  }

  async function copyOutput() {
    try {
      await navigator.clipboard.writeText(toPlainText());
      copied = true;
      setTimeout(() => (copied = false), 2000);
    } catch {
      /* clipboard may be unavailable */
    }
  }
</script>

<div class="flex h-full flex-col bg-slate-950">
  <!-- Toolbar -->
  <div
    class="flex flex-shrink-0 items-center justify-between border-b border-slate-700/50 bg-slate-900 px-4 py-2"
  >
    <div class="flex items-center gap-2">
      <div class="flex gap-1.5">
        <span class="inline-block h-3 w-3 rounded-full bg-slate-700"></span>
        <span class="inline-block h-3 w-3 rounded-full bg-slate-700"></span>
        <span class="inline-block h-3 w-3 rounded-full bg-slate-700"></span>
      </div>
      <span class="ml-1 font-mono text-xs text-slate-600">output</span>
    </div>

    <div class="flex items-center gap-3">
      {#if running}
        <span class="flex items-center gap-1.5 text-xs text-amber-400">
          <span class="inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-amber-400"></span>
          Running
        </span>
      {:else if events.length > 0}
        <span class="flex items-center gap-1.5 text-xs text-emerald-400">
          <span class="inline-block h-1.5 w-1.5 rounded-full bg-emerald-400"></span>
          Complete
        </span>
      {/if}

      {#if events.length > 0}
        <button
          onclick={copyOutput}
          class="flex items-center gap-1.5 rounded px-2 py-1 text-xs transition-colors
            {copied
            ? 'bg-emerald-800/60 text-emerald-300'
            : 'bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200'}"
        >
          {#if copied}
            <svg class="h-3.5 w-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
            </svg>
            Copied!
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
      {/if}
    </div>
  </div>

  <!-- Output area -->
  <div bind:this={consoleEl} class="console-font flex-1 overflow-y-auto p-5">
    {#if events.length === 0}
      <div class="flex h-full items-center justify-center">
        <div class="text-center text-slate-700">
          <div class="mb-2 text-4xl">▶</div>
          <p class="text-sm">Select a mode and click Execute to begin</p>
        </div>
      </div>
    {:else}
      {#each events as event}

        {#if event.type === "start"}
          <div class="mb-3 text-slate-600">
            ── Starting:
            {#if event.total_ping_tests > 0}
              {event.total_ping_tests} ping test{event.total_ping_tests !== 1 ? "s" : ""},
            {/if}
            {#if event.total_command_tests > 0}
              {event.total_command_tests} command test{event.total_command_tests !== 1 ? "s" : ""}
              across {event.total_devices} device{event.total_devices !== 1 ? "s" : ""}
            {/if}
             ──
          </div>

        {:else if event.type === "ping_section"}
          <div class="mt-5 mb-2 text-slate-500">── Host Pings ──</div>

        {:else if event.type === "ping_test_start"}
          <div class="mt-2 mb-1">
            <span class="font-semibold text-violet-400">[HOST]</span>
            <span class="ml-1 text-slate-200">{event.test}</span>
            <span class="ml-2 text-xs text-slate-600">
              {event.destinations?.length} destination{event.destinations?.length !== 1 ? "s" : ""},
              count={event.count}
            </span>
          </div>

        {:else if event.type === "ping_result"}
          <div class="mt-2 ml-2">
            <div class="mb-0.5 flex items-center gap-2">
              <span class="text-slate-600">$</span>
              <span class="text-yellow-400">ping {event.destination}</span>
              {#if event.success}
                <span class="rounded bg-emerald-900/60 px-1.5 py-0.5 text-xs text-emerald-400">reachable</span>
              {:else}
                <span class="rounded bg-red-900/60 px-1.5 py-0.5 text-xs text-red-400">unreachable</span>
              {/if}
            </div>
            <pre
              class="ml-3 whitespace-pre-wrap break-words border-l-2 pl-3 text-sm
                {event.success ? 'border-emerald-800 text-slate-300' : 'border-red-900 text-red-300'}"
            >{event.output}</pre>
          </div>

        {:else if event.type === "device_section"}
          <div class="mt-6 mb-2 text-slate-500">── Device Tests ──</div>

        {:else if event.type === "device_start"}
          <div class="mt-5 mb-1">
            <span class="font-semibold text-cyan-400">[{event.device}]</span>
            <span class="text-slate-500"> Connecting to </span>
            <span class="text-slate-300">{event.host}</span>
            <span class="text-slate-600">…</span>
          </div>

        {:else if event.type === "test_result"}
          <div class="mt-3">
            <div class="mb-0.5">
              <span class="text-cyan-400">[{event.device}]</span>
              <span class="text-slate-600"> $ </span>
              <span class="text-yellow-400">{event.command}</span>
            </div>
            <pre
              class="ml-1 whitespace-pre-wrap break-words border-l-2 border-slate-700 pl-3 text-slate-300"
            >{event.output}</pre>
          </div>

        {:else if event.type === "device_error"}
          <div class="mt-2">
            <span class="text-red-400">[{event.device}] ERROR:</span>
            <span class="ml-1 text-red-300">{event.message}</span>
          </div>

        {:else if event.type === "device_complete"}
          <div class="mt-1 text-xs text-slate-700">[{event.device}] session closed</div>

        {:else if event.type === "complete"}
          <div class="mt-5 text-slate-500">
            ── {event.saved ? `Saved as ${event.mode} snapshot` : "Complete"} ──
          </div>

        {:else if event.type === "error"}
          <div class="mt-2 text-red-400">ERROR: {event.message}</div>
        {/if}

      {/each}

      {#if running}
        <div class="mt-2 animate-pulse text-slate-500">▌</div>
      {/if}
    {/if}
  </div>
</div>
