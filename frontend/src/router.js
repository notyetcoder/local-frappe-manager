import { createRouter, createWebHistory } from 'vue-router'

const routes = [
	{
		path: '/',
		redirect: '/apps',
	},
	{
		path: '/apps',
		name: 'Apps',
		component: () => import('@/pages/Apps.vue'),
	},
	{
		path: '/sites',
		name: 'Sites',
		component: () => import('@/pages/Sites.vue'),
	},
]

const router = createRouter({
	history: createWebHistory('/local-bench/'),
	routes,
})

export default router
