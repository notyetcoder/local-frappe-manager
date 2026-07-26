<template>
	<FrappeUIProvider>
		<Welcome v-if="showWelcome" @done="onWelcomeDone" />
		<div v-else class="flex h-screen w-screen overflow-hidden bg-surface-white">
			<aside class="flex w-56 flex-shrink-0 flex-col border-r bg-surface-gray-1 p-3">
				<div class="mb-6 px-2 pt-2 text-lg font-semibold text-ink-gray-9">
					local-bench
				</div>
				<nav class="flex flex-col gap-1">
					<router-link
						v-for="item in navItems"
						:key="item.path"
						:to="item.path"
						class="rounded px-3 py-2 text-sm font-medium text-ink-gray-6 hover:bg-surface-gray-3"
						active-class="bg-surface-gray-3 text-ink-gray-9"
					>
						{{ item.label }}
					</router-link>
				</nav>
			</aside>
			<main class="flex-1 overflow-y-auto p-8">
				<router-view />
			</main>
		</div>
	</FrappeUIProvider>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Welcome from '@/pages/Welcome.vue'
import api from '@/data/api'

const navItems = [
	{ path: '/apps', label: 'Apps' },
	{ path: '/sites', label: 'Sites' },
]

// Default to true so we never flash the main dashboard before we know
// whether this is actually a first run.
const showWelcome = ref(true)
const checked = ref(false)

onMounted(async () => {
	try {
		showWelcome.value = !(await api.getWelcomeSeen())
	} catch (e) {
		// If the check itself fails (e.g. not logged in yet), fail safe by
		// not blocking the dashboard behind a broken welcome screen.
		showWelcome.value = false
	}
	checked.value = true
})

async function onWelcomeDone() {
	await api.markWelcomeSeen()
	showWelcome.value = false
}
</script>
