import { call } from 'frappe-ui'

const METHOD_PREFIX = 'local_bench.api.'

function api(method) {
	return (args) => call(METHOD_PREFIX + method, args)
}

export default {
	getWelcomeSeen: api('get_welcome_seen'),
	markWelcomeSeen: api('mark_welcome_seen'),

	listSites: api('list_sites'),
	listInstalledAppsOnBench: api('list_installed_apps_on_bench'),
	listGalleryApps: api('list_gallery_apps'),

	installApp: api('install_app'),
	uninstallApp: api('uninstall_app'),
	newSite: api('new_site'),
	backupSite: api('backup_site'),
	restoreBackup: api('restore_backup'),
	migrateSite: api('migrate_site'),
	dropSite: api('drop_site'),
}
