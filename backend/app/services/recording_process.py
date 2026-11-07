"""Owned FFmpeg child: EOF on the control pipe always tears down its group.

Executed as a module, never a shell. Parent passes already-open output/input
file descriptors. The child does not discover processes or filesystem paths.
"""
import os
import ctypes
import selectors
import signal
import subprocess
import sys
import time


def supervise(control, output, ownership, argv):
    parent_pid = os.getpid()
    def parent_death():
        if sys.platform.startswith('linux'):
            ctypes.CDLL(None, use_errno=True).prctl(1, signal.SIGKILL)
            if os.getppid() != parent_pid:
                os.kill(os.getpid(), signal.SIGKILL)

    process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=output,
                               stderr=subprocess.PIPE, start_new_session=True, close_fds=True,
                               preexec_fn=parent_death,
                               pass_fds=tuple(int(a[8:]) for a in argv if a.startswith('/dev/fd/') and a[8:].isdigit()) + ((ownership,) if ownership >= 0 else ()))
    selector = selectors.DefaultSelector()
    selector.register(control, selectors.EVENT_READ, 'control')
    selector.register(process.stderr, selectors.EVENT_READ, 'progress')
    stopped = False

    def stop(*_):
        nonlocal stopped
        stopped = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while process.poll() is None and not stopped:
            for key, _ in selector.select(.2):
                chunk = os.read(key.fd, 4096)
                if key.data == 'control':
                    if not chunk:
                        stopped = True
                elif chunk:
                    try:
                        os.write(sys.stdout.fileno(), chunk)
                    except BrokenPipeError:
                        stopped = True
                else:
                    selector.unregister(key.fileobj)
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=1.5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
        return process.wait()
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait()
        selector.close()
        process.stderr.close()


if __name__ == '__main__':
    sys.exit(supervise(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]))
