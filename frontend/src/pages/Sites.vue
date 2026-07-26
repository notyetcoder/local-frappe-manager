<template>
	<div>
		<h1 class="mb-6 text-lg font-semibold text-ink-gray-9">Sites</h1>

		<div class="space-y-3">
			<Card v-for="site in sites" :key="site.name" :title="site.name">
				<template #actions>
					<Button size="sm" @click="run(backupHandler, site.name)">Backup</Button>
					<Button size="sm" @click="run(migrateHandler, site.name)">Migrate</Button>
					<Button size="sm" theme="red" variant="outline" @click="confirmDrop(site.name)">
						Drop
					</Button>
				</template>
				<div class="flex flex-wrap gap-1">
					<Badge v-for="app in site.apps" :key="app" theme="gray">{{ app }}</Badge>
					<span v-if="!site.apps.length" class="text-sm text-ink-gray-5">No apps installed</span>
				</div>
			</Card>
			<p v-if="!sites.length" class="text-sm text-ink-gray-5">
				No sites yet — install an app from the Apps tab to create your first one.
			</p>
		</div>

		<Dialog v-model="showActionDialog" :options="{ title: actionTitle, size: 'md' }">
			<template #body-content>
				<LogPanel v-if="activeChannel" :channel="activeChannel" @finished="refresh" />
			</template>
		</Dialog>

		<Dialog v-model="showDropConfirm" :options="{ title: 'Drop site?', size: 'sm' }">
			<template #body-content>
				<p class="text-sm text-ink-gray-6">
					This deletes <b>{{ siteToDrop }}</b> after taking an automatic
					backup first. This can't be undone from here.
				</p>
				<div class="mt-4 flex justify-end gap-2">
					<Button variant="outline" @click="showDropConfirm = false">Cancel</Button>
					<Button theme="red" variant="solid" @click="doDrop">Drop site</Button>
				</div>
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Card, Badge, Button, Dialog } from 'frappe-ui'
import LogPanel from '@/components/LogPanel.vue'
import api from '@/data/api'

const sites = ref([])
const showActionDialog = ref(false)
const activeChannel = ref(null)
const actionTitle = ref('')

const showDropConfirm = ref(false)
const siteToDrop = ref(null)

async function refresh() {
	sites.value = await api.listSites()
}

async function run(handler, site) {
	actionTitle.value = handler.title
	const { channel } = await handler.call(site)
	activeChannel.value = channel
	showActionDialog.value = true
}

const backupHandler = {
	title: 'Backing up',
	call: (site) => api.backupSite({ site }),
}
const migrateHandler = {
	title: 'Migrating',
	call: (site) => api.migrateSite({ site }),
}

function confirmDrop(site) {
	siteToDrop.value = site
	showDropConfirm.value = true
}

async function doDrop() {
	showDropConfirm.value = false
	actionTitle.value = 'Dropping site'
	const { channel } = await api.dropSite({ site: siteToDrop.value })
	activeChannel.value = channel
	showActionDialog.value = true
}

onMounted(refresh)
</script>
