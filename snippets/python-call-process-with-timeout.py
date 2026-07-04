import subprocess
import select
import threading
import logging
from py_logging import init_logging

def call_process_with_timeout(cmd_list, debug_mode=True, shell=False, env=None, timeout_secs=1800):
    try:
        proc = subprocess.Popen(cmd_list,
                                env=env,
                                universal_newlines=True,
                                shell=shell,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)

        def kill_proc(p, p_name):
            nonlocal timed_out
            if p.poll() is None:
                p.terminate()
                timed_out = True
                logging.error(
                    "Process {} terminated due to timeout".format(p_name))

        p_name = subprocess.list2cmdline(cmd_list)
        timer = threading.Timer(timeout_secs, kill_proc, [proc, p_name])
        timer.start()
        result = ""
        timed_out = False

        while True:
            ready, _, _ = select.select([proc.stdout], [], [], 5)
            if ready:
                line = proc.stdout.readline()
                result += line
                if debug_mode:
                    logging.info(line.strip())
                if not line:  # EOF
                    logging.info("[debug] meet EOF, start to poll")
                    returncode = proc.poll()
                    if returncode is not None:
                        logging.info("[debug] successful break")
                        break
                    time.sleep(0.1)  # cmd closed stdout, but not exited yet
                    logging.info("[debug] cmd closed stdout, but not exited yet")
            else:
                returncode = proc.poll()
                if returncode is not None:
                    break
                else:
                    logging.info("[debug] Waiting for output...")
        timer.cancel()
        return returncode == 0 and not timed_out
    except subprocess.CalledProcessError as e:
        logging.exception('Call process {} error: {}'.format(p_name,
            e.output))
        return False
    except IOError:
        logging.exception('Call process {} error: script not found'.format(p_name))
        return False
    except Exception as e:
        logging.exception("Call process {} error: {}".format(p_name, str(e)))
        return False

def main():
    cmd_list = ["sleep 30"]
    cmd_list.extend(["&&", "ls"])
    call_process_with_timeout(cmd_list, shell=True)


if __name__ == '__main__':
    log_file = './tmp.log'
    init_logging(log_file)
    main()