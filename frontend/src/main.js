import { createApp } from 'vue'
import { FrappeUIProvider, setConfig, frappeRequest } from 'frappe-ui'
import App from './App.vue'
import router from './router'
import './index.css'

setConfig('resourceFetcher', frappeRequest())

const app = createApp(App)
app.use(router)
app.component('FrappeUIProvider', FrappeUIProvider)
app.mount('#app')
