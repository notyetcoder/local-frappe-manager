<template>
	<div>
		<div class="mb-6 flex items-center justify-between">
			<h1 class="text-lg font-semibold text-ink-gray-9">Apps</h1>
			<Button variant="outline" @click="openCustomDialog">
				Install from GitHub URL
			</Button>
		</div>

		<div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
			<Card
				v-for="app in gallery"
				:key="app.app_name"
				:title="app.title"
				:subtitle="app.description"
			>
				<template #actions>
					<Badge v-if="isInstalled(app.app_name)" theme="green">Installed</Badge>
					<Button v-else variant="solid" @click="openInstallDialog(app)">
						Install
					</Button>
				</template>
			</Card>
		</div>

		<!-- Install-from-gallery dialog -->
		<Dialog v-model="showInstallDialog" :options="{ title: `Install ${selectedApp?.title || ''}`, size: 'md' }">
			<template #body-content>
				<div v-if="!activeChannel" class="space-y-4">
					<FormControl
						label="Site name"
						v-model="form.site"
						description="Where this app will be installed. Uses .localhost so no setup is needed to access it."
					/>
					<FormControl
						label="Administrator password"
						v-model="form.password"
						description="Auto-generated. Change it if you'd like, or leave as-is."
					/>
					<Button variant="solid" class="w-full" @click="submitInstall">
						Install {{ selectedApp?.title }}
					</Button>
				</div>
				<div v-else>
					<p class="text-sm text-ink-gray-6">
						Installing on <b>{{ form.site }}</b>. Admin password:
						<code class="rounded bg-surface-gray-2 px-1 py-0.5">{{ form.password }}</code>
						— save this now, it won't be shown again.
					</p>
					<LogPanel :channel="activeChannel" @finished="onInstallFinished" />
				</div>
			</template>
		</Dialog>

		<!-- Install-from-URL dialog -->
		<Dialog v-model="showCustomDialog" :options="{ title: 'Install from GitHub URL', size: 'md' }">
			<template #body-content>
				<div v-if="!customChannel" class="space-y-4">
					<FormControl
						label="GitHub URL"
						v-model="customForm.repoUrl"
						placeholder="https://github.com/someone/their-frappe-app"
					/>
					<FormControl
						label="App name"
						v-model="customForm.appName"
						description="Must match the app's actual name (usually the last part of the repo URL, e.g. 'their-frappe-app')"
					/>
					<FormControl label="Site name" v-model="customForm.site" />
					<FormControl label="Administrator password" v-model="customForm.password" />
					<p class="text-xs text-ink-gray-5">
						Third-party apps aren't reviewed by us. Only install apps you
						trust — installing an app runs its code on your machine, same
						as running <code>bench get-app</code> directly would.
					</p>
					<Button variant="solid" class="w-full" @click="submitCustomInstall">
						Install
					</Button>
				</div>
				<LogPanel v-else :channel="customChannel" @finished="onCustomInstallFinished" />
			</template>
		</Dialog>
	</div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Card, Badge, Button, Dialog, FormControl, toast } from 'frappe-ui'
import LogPanel from '@/components/LogPanel.vue'
import api from '@/data/api'

const gallery = ref([])
const sites = ref([])

const showInstallDialog = ref(false)
const selectedApp = ref(null)
const activeChannel = ref(null)
const form = ref({ site: '', password: '' })
// 'site' -> creating a bare site, 'app' -> fetching + installing the app onto it
const installStage = ref('site')

const showCustomDialog = ref(false)
const customChannel = ref(null)
const customForm = ref({ repoUrl: '', appName: '', site: '', password: '' })
// 'site' -> creating the site, 'app' -> installing the app onto it, 'done'
const customStage = ref('site')

function defaultPassword() {
	return 'frappeP'
}

function isInstalled(appName) {
	return sites.value.some((s) => s.apps.includes(appName))
}

async function refresh() {
	const [g, siteList] = await Promise.all([api.listGalleryApps(), api.listSites()])
	gallery.value = g
	sites.value = siteList
}

function openInstallDialog(app) {
	selectedApp.value = app
	activeChannel.value = null
	installStage.value = 'site'
	form.value = {
		site: `${app.app_name}.localhost`,
		password: defaultPassword(),
	}
	showInstallDialog.value = true
}

async function submitInstall() {
	installStage.value = 'site'
	const { channel } = await api.newSite({
		site: form.value.site,
		admin_password: form.value.password,
	})
	activeChannel.value = channel
}

async function onInstallFinished(success) {
	if (!success) return

	if (installStage.value === 'site') {
		// Site created (bare) — now fetch and install the actual app. Apps
		// outside the base image (which is intentionally minimal — see the
		// installer's README) aren't pre-fetched, so this always needs an
		// explicit get-app step, same as the "install from URL" flow.
		installStage.value = 'app'
		const { channel } = await api.installApp({
			app: selectedApp.value.app_name,
			site: form.value.site,
			repo_url: selectedApp.value.repo,
		})
		activeChannel.value = channel
	} else if (installStage.value === 'app') {
		installStage.value = 'done'
		toast({ title: `${selectedApp.value.title} installed`, icon: 'check', iconClasses: 'text-ink-green-3' })
		refresh()
	}
}

function openCustomDialog() {
	customChannel.value = null
	customStage.value = 'site'
	customForm.value = { repoUrl: '', appName: '', site: '', password: '' }
	showCustomDialog.value = true
}

function submitCustomInstall() {
	if (!customForm.value.site) customForm.value.site = `${customForm.value.appName}.localhost`
	if (!customForm.value.password) customForm.value.password = defaultPassword()
	installCustom()
}

async function installCustom() {
	customStage.value = 'site'
	const { channel } = await api.newSite({
		site: customForm.value.site,
		admin_password: customForm.value.password,
	})
	customChannel.value = channel
}

async function onCustomInstallFinished(success) {
	if (!success) return

	if (customStage.value === 'site') {
		// Site created — now fetch and install the actual app onto it.
		customStage.value = 'app'
		const { channel } = await api.installApp({
			app: customForm.value.appName,
			site: customForm.value.site,
			repo_url: customForm.value.repoUrl,
		})
		customChannel.value = channel
	} else if (customStage.value === 'app') {
		customStage.value = 'done'
		toast({ title: `${customForm.value.appName} installed`, icon: 'check', iconClasses: 'text-ink-green-3' })
		refresh()
	}
}

onMounted(refresh)
</script>
