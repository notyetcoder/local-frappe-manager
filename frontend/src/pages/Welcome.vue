<template>
	<div class="flex h-screen w-screen items-center justify-center bg-surface-gray-1">
		<div class="max-w-lg rounded-xl border bg-surface-white p-8 shadow-sm">
			<h1 class="text-xl font-semibold text-ink-gray-9">Welcome to local-bench</h1>
			<p class="mt-3 text-sm leading-relaxed text-ink-gray-6">
				This is your local Frappe bench, managed from the browser. From
				here you can:
			</p>
			<ul class="mt-3 list-inside list-disc space-y-1 text-sm text-ink-gray-6">
				<li>Install apps like ERPNext, CRM, or HR with one click</li>
				<li>Install any other Frappe-compatible app from its GitHub URL</li>
				<li>Manage sites — backup, restore, migrate, or remove them</li>
			</ul>
			<p class="mt-3 text-sm leading-relaxed text-ink-gray-6">
				Everything here runs real <code class="rounded bg-surface-gray-2 px-1 py-0.5">bench</code>
				commands on your machine — nothing is sent to any external
				server. What this doesn't do (yet): host your sites on the
				internet or manage multiple remote servers. That's a possible
				future phase, not this one.
			</p>
			<Button variant="solid" class="mt-6 w-full" @click="$emit('done')">
				Get started
			</Button>
		</div>
	</div>
</template>

<script setup>
import { Button } from 'frappe-ui'
defineEmits(['done'])
</script>
