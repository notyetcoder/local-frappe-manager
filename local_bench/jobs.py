"""
Runs `bench` commands as background jobs and streams their output back to
the browser in real time over Socketio.

Nothing here is Frappe-Cloud-style container orchestration — it's a thin,
honest wrapper around the same `bench` commands you'd type yourself. That's
deliberate: it's the smallest amount of backend needed to make the buttons
in the dashboard real, and it's easy to read top-to-bottom and trust.
"""

import subprocess

import frappe
from frappe.utils import get_bench_path


def run_bench_command(command: list[str], channel: str, site: str | None = None):
	"""
	Run a bench command, streaming stdout/stderr line-by-line to the given
	realtime channel, and publish a final status event when it's done.

	command: e.g. ["new-site", "erpnext.localhost", "--install-app", "erpnext"]
	         (without the leading "bench" — that's added here)
	channel: a unique string the frontend subscribes to via
	         frappe.realtime.on(channel, ...) to display live logs
	site:    if given, runs as `bench --site <site> <command>` instead of a
	         bench-wide command
	"""
	full_command = ["bench"]
	if site:
		full_command += ["--site", site]
	full_command += command

	frappe.publish_realtime(
		channel, {"type": "start", "command": " ".join(full_command)}
	)

	try:
		process = subprocess.Popen(
			full_command,
			cwd=get_bench_path(),
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
			text=True,
			bufsize=1,
		)

		assert process.stdout is not None
		for line in process.stdout:
			frappe.publish_realtime(channel, {"type": "log", "line": line.rstrip()})

		process.wait()

		if process.returncode == 0:
			frappe.publish_realtime(channel, {"type": "done", "success": True})
		else:
			frappe.publish_realtime(
				channel,
				{
					"type": "done",
					"success": False,
					"message": f"Command exited with code {process.returncode}. "
					"Scroll up in the log for the actual error.",
				},
			)

	except Exception as e:
		frappe.log_error(title="local_bench command failed", message=frappe.get_traceback())
		frappe.publish_realtime(
			channel, {"type": "done", "success": False, "message": str(e)}
		)
