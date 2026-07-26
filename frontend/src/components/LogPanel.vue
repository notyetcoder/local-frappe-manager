<template>
	<div class="mt-3 overflow-hidden rounded-lg border">
		<div class="flex items-center justify-between border-b bg-surface-gray-1 px-3 py-2">
			<div class="flex items-center gap-2 text-sm font-medium text-ink-gray-7">
				<LoadingIndicator v-if="running" class="h-4 w-4" />
				<FeatherIcon
					v-else
					:name="success ? 'check-circle' : 'x-circle'"
					class="h-4 w-4"
					:class="success ? 'text-ink-green-3' : 'text-ink-red-3'"
				/>
				{{ statusText }}
			</div>
		</div>
		<pre
			ref="logEl"
			class="max-h-64 overflow-y-auto bg-ink-gray-9 p-3 font-mono text-xs text-ink-gray-1"
		>{{ lines.join('\n') }}</pre>
	</div>
</template>

<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { LoadingIndicator, FeatherIcon } from 'frappe-ui'
import { subscribeToJob } from '@/data/socket'

const props = defineProps({
	channel: { type: String, required: true },
})
const emit = defineEmits(['finished'])

const lines = ref([])
const running = ref(true)
const success = ref(null)
const logEl = ref(null)
let unsubscribe = null

const statusText = ref('Running...')

function attach(channel) {
	unsubscribe?.()
	lines.value = []
	running.value = true
	success.value = null
	statusText.value = 'Running...'

	unsubscribe = subscribeToJob(channel, (data) => {
		if (data.type === 'start') {
			lines.value.push(`$ ${data.command}`)
		} else if (data.type === 'log') {
			lines.value.push(data.line)
		} else if (data.type === 'done') {
			running.value = false
			success.value = data.success
			statusText.value = data.success
				? 'Done'
				: data.message || 'Something went wrong'
			emit('finished', data.success)
		}
		nextTick(() => {
			if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight
		})
	})
}

watch(() => props.channel, attach, { immediate: true })
onBeforeUnmount(() => unsubscribe?.())
</script>
