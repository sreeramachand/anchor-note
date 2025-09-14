"""
Windows service socket wrapper — lightweight loopback server that allows GUI agent(s) to receive
alerts from the service. The actual service logic runs in core.scheduler.Scheduler.

This file exposes a ServiceFramework implementation (pywin32) that boots a LocalSocketServer
and the Scheduler. The GUI agent connects to the socket to receive alerts (JSON per-line).
"""

import json
import logging
import socket
import threading
import time
from datetime import datetime, timezone

# windows_service_socket.py (top)
try:
    import win32serviceutil  # type: ignore
    import win32service      # type: ignore
    import win32event        # type: ignore
    import servicemanager    # type: ignore
except Exception:
    # When not on Windows (or when pywin32 is not installed) the imports fail.
    # Use guards in the rest of the module to avoid calling None values.
    win32serviceutil = None
    win32service = None
    win32event = None
    servicemanager = None

# pywin32 imports guarded (module only needed when run as service on Windows)

from ..core.scheduler import Scheduler
from ..core.checklist import list_pending_tasks

LOG = logging.getLogger(__name__)
HOST = "127.0.0.1"
PORT = 8765

class LocalSocketServer(threading.Thread):
    def __init__(self, host=HOST, port=PORT):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self._stop = threading.Event()
        self.sock = None
        self.clients = []

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(5)
        self.sock.settimeout(1.0)
        LOG.info("Socket server listening on %s:%d", self.host, self.port)
        while not self._stop.is_set():
            try:
                conn, addr = self.sock.accept()
                conn.settimeout(1.0)
                self.clients.append(conn)
                threading.Thread(target=self._client_reader, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                LOG.exception("socket accept")

        # cleanup
        for c in self.clients:
            try:
                c.close()
            except Exception:
                pass
        try:
            self.sock.close()
        except Exception:
            pass

    def _client_reader(self, conn):
        try:
            buf = b""
            while not self._stop.is_set():
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                    buf += data
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        try:
                            obj = json.loads(line.decode("utf-8"))
                            # simple ack handling could be implemented here
                        except Exception:
                            pass
                except socket.timeout:
                    continue
        finally:
            try:
                conn.close()
            except Exception:
                pass
            if conn in self.clients:
                self.clients.remove(conn)

    def broadcast(self, obj: dict):
        msg = (json.dumps(obj) + "\n").encode("utf-8")
        dead = []
        for c in list(self.clients):
            try:
                c.sendall(msg)
            except Exception:
                dead.append(c)
                try:
                    c.close()
                except Exception:
                    pass
        for d in dead:
            if d in self.clients:
                self.clients.remove(d)

    def stop(self):
        self._stop.set()

# Basic service wrapper for Windows using pywin32
if win32serviceutil:
    class StickyService(win32serviceutil.ServiceFramework):
        _svc_name_ = "AnchorNoteService"
        _svc_display_name_ = "Anchor Note Service"

        def __init__(self, args):
            win32serviceutil.ServiceFramework.__init__(self, args)
            self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
            self._stop = threading.Event()
            self.server = LocalSocketServer()
            self.scheduler = Scheduler()
            self._thread = None

        def SvcStop(self):
            self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
            self._stop.set()
            try:
                self.scheduler.stop()
            except Exception:
                pass
            try:
                self.server.stop()
            except Exception:
                pass
            win32event.SetEvent(self.hWaitStop)

        def SvcDoRun(self):
            servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                                  servicemanager.PYS_SERVICE_STARTED,
                                  (self._svc_name_, ""))
            # start socket server and scheduler
            self.server.start()
            self.scheduler.start()

            # poll loop: broadcast due tasks to connected clients
            try:
                while not self._stop.is_set():
                    now_ts = int(datetime.now(timezone.utc).timestamp())
                    rows = list_pending_tasks()
                    for t in rows:
                        if t["end"] and t["end"].timestamp() <= now_ts and t["status"] != "done":
                            payload = {
                                "type": "alert",
                                "task_id": t["id"],
                                "uid": t["uid"],
                                "title": t["title"],
                                "start_ts": int(t["start"].timestamp()) if t["start"] else 0,
                                "end_ts": int(t["end"].timestamp()) if t["end"] else 0,
                                "red": 1 if t["red"] else 0
                            }
                            self.server.broadcast(payload)
                    time.sleep(5)
            finally:
                self.server.stop()
                self.scheduler.stop()

# If not running as service (e.g., running on non-Windows), provide a simple main for testing
def main():
    srv = LocalSocketServer()
    srv.start()
    sched = Scheduler()
    sched.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        srv.stop()
        sched.stop()

if __name__ == "__main__":
    main()
