import { initSocket } from 'frappe-ui'

let socket = null

export function getSocket() {
	if (!socket) {
		socket = initSocket()
	}
	return socket
}

/**
 * Subscribe to a local_bench job channel. Calls onEvent for every
 * {type: 'start'|'log'|'done', ...} message published by jobs.py, and
 * automatically unsubscribes once a 'done' event arrives.
 *
 * Returns an unsubscribe function in case the component unmounts early.
 */
export function subscribeToJob(channel, onEvent) {
	const s = getSocket()

	function handler(data) {
		onEvent(data)
		if (data.type === 'done') {
			s.off(channel, handler)
		}
	}

	s.on(channel, handler)
	return () => s.off(channel, handler)
}
