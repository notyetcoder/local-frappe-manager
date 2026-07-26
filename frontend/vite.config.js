import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import frappeui from 'frappe-ui/vite'
import path from 'path'

// frontendRoute must match the base used in src/router.js. frappe-ui's
// buildConfig plugin uses this to know where to write the built HTML
// entry point (local_bench/www/local-bench.html) so Frappe serves it at
// http://<site>/local-bench with no extra www/*.py boilerplate needed.
export default defineConfig({
	plugins: [
		frappeui({
			frontendRoute: '/local-bench',
			buildConfig: {
				indexHtmlPath: '../local_bench/www/local-bench.html',
				baseUrl: '/assets/local_bench/frontend/',
			},
		}),
		vue(),
	],
	resolve: {
		alias: {
			'@': path.resolve(__dirname, 'src'),
		},
	},
})
