#/usr/bin/python
# -*- encoding=utf-8 -*-

import os
import logging
import subprocess


def run_cmd_with_output(cmd,
                        shell=True,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        background=False,
                        out_lines=True):
    """
    :param cmd:
    :param stdout: None will display output to sys stdout
    :param stderr: None will display output to sys stderr
    :return:
    """

    def split_lines(lines):
        if lines:
            return [x for x in lines.split('\n') if x]
        return lines

    process = subprocess.Popen(cmd,
                               shell=shell,
                               env=os.environ.copy(),
                               preexec_fn=os.setsid if background else None,
                               stdout=stdout,
                               stderr=stderr)
    out, err = process.communicate()
    ret = process.returncode
    if ret != 0:
        logging.error(
            "[run_cmd_with_output], cmd: {} ret: {}, out: {}, err:{} ".format(
                cmd, ret, out, err))
    if out_lines:
        return ret, split_lines(out)
    else:
        return ret, out


class HDFS(object):
    '''Fundamental class for HDFS basic manipulation
    '''

    @staticmethod
    def exists(uri):
        '''Check existence of hdfs uri
        Returns: True on exists
        Raises: RuntimeError
        '''
        hadoop_bin = HDFS._hadoop_bin(uri)
        cmd = '{hbin} fs -test -e {uri}'.format(hbin=hadoop_bin, uri=uri)
        try:
            ret, out = run_cmd_with_output(cmd)
            if ret == 0:
                return True
            elif ret == 1:
                return False
            else:
                raise RuntimeError('Cannot check existence of hdfs uri[{}] '
                                   'with cmd[{}]; ret[{}] output[{}]'.format(
                                       uri, cmd, ret, out))
        except Exception as e:
            raise RuntimeError('Cannot check existence of hdfs uri[{}] '
                               'with cmd[{}] on unexpected error[{}]'.format(
                                   uri, cmd, repr(e)))

    @staticmethod
    def remove(uri):
        '''Check existence of hdfs uri
        Returns: True on exists
        Raises: RuntimeError
        '''
        hadoop_bin = HDFS._hadoop_bin(uri)
        cmd = '{hbin} fs -rm -r {uri}'.format(hbin=hadoop_bin, uri=uri)
        try:
            ret, out = run_cmd_with_output(cmd)
            if ret == 0:
                return True
            elif ret == 1:
                return False
            else:
                raise RuntimeError('Cannot remove hdfs uri[{}] '
                                   'with cmd[{}]; ret[{}] output[{}]'.format(
                                       uri, cmd, ret, out))
        except Exception as e:
            raise RuntimeError('Cannot remove hdfs uri[{}] '
                               'with cmd[{}] on unexpected error[{}]'.format(
                                   uri, cmd, repr(e)))

    @staticmethod
    def mkdir(uri):
        '''Make new hdfs directory
        Returns: True on success
        Raises: RuntimeError
        '''
        hadoop_bin = HDFS._hadoop_bin(uri)
        cmd = '{hbin} fs -mkdir -p {uri}'.format(hbin=hadoop_bin, uri=uri)

        try:
            ret, out = run_cmd_with_output(cmd)
            if ret == 0:
                return True
            elif ret == 1:
                return False
            else:
                raise RuntimeError('Cannot mkdir of hdfs uri[{}] '
                                   'with cmd[{}]; ret[{}] output[{}]'.format(
                                       uri, cmd, ret, out))
        except Exception as e:
            raise RuntimeError('Cannot mkdir of hdfs uri[{}] '
                               'with cmd[{}] on unexpected error[{}]'.format(
                                   uri, cmd, repr(e)))

    @staticmethod
    def move(from_uri, to_uri):
        '''Move HDFS uri
        Returns: True on success
        Raises: RuntimeError
        '''
        if from_uri.split(':')[0].strip() != to_uri.split(':')[0].strip():
            raise RuntimeError('from_uri[{}] takes with different prefix '
                               'compared to to_uri[{}]'.format(
                                   from_uri, to_uri))

        hadoop_bin = HDFS._hadoop_bin(from_uri)
        cmd = '{hbin} fs -mv {furi} {turi}'.format(hbin=hadoop_bin,
                                                   furi=from_uri,
                                                   turi=to_uri)
        try:
            ret, out = run_cmd_with_output(cmd)
            if ret == 0:
                return True
            elif ret == 1:
                return False
            else:
                raise RuntimeError('Cannot move from_uri[{}] to '
                                   'to_uri[{}] with cmd[{}]; '
                                   'ret[{}] output[{}]'.format(
                                       from_uri, to_uri, cmd, ret, out))
        except Exception as e:
            raise RuntimeError('Cannot move from_uri[{}] to '
                               'to_uri[{}] with cmd[{}] '
                               'on unexpected error[{}]'.format(
                                   from_uri, to_uri, cmd, repr(e)))

    @staticmethod
    def copy_from_local(local_path, to_uri):
        '''
        Returns: True on success
        Raises: on unexpected error
        '''
        # Make sure local_path is accessible
        if not os.path.exists(local_path) or \
            not os.access(local_path, os.R_OK):
            raise RuntimeError('try to access local_path[{}] '
                               'but failed'.format(local_path))

        hadoop_bin = HDFS._hadoop_bin(to_uri)
        cmd = '{hbin} fs -copyFromLocal {local} {remote}'.format(
            hbin=hadoop_bin, local=local_path, remote=to_uri)
        try:
            ret, out = run_cmd_with_output(cmd)
            if ret == 0:
                return True
            elif ret == 1:
                return False
            else:
                raise RuntimeError('Cannot copy local[{}] '
                                   'to remote[{}] with cmd[{}]; '
                                   'ret[{}] output[{}]'.format(
                                       local_path, to_uri, cmd, ret, out))
        except Exception as e:
            raise RuntimeError('Cannot copy local[{}] '
                               'to remote[{}] with cmd[{}] '
                               'on error[{}]'.format(local_path, to_uri, cmd,
                                                     repr(e)))

    @staticmethod
    def copy_to_local(from_uri, local_path):
        # Make sure local_path is accessible
        if not os.path.exists(local_path) or \
            not os.access(local_path, os.R_OK):
            raise RuntimeError('try to access local_path[{}] '
                               'but failed'.format(local_path))

        if isinstance(from_uri, str):
            remote = from_uri
        elif isinstance(from_uri, list) or \
             isinstance(from_uri, tuple):
            remote = ' '.join(from_uri)
        hadoop_bin = HDFS._hadoop_bin(remote)
        cmd = '{hbin} fs -copyToLocal {remote} {local}'.format(
            hbin=hadoop_bin, remote=remote, local=local_path)

        try:
            ret, out = run_cmd_with_output(cmd)
            if ret == 0:
                return True
            elif ret == 1:
                return False
            else:
                raise RuntimeError('Cannot copy remote[{}] '
                                   'to local[{}] with cmd[{}]; '
                                   'ret[{}] output[{}]'.format(
                                       from_uri, local_path, cmd, ret, out))
        except Exception as e:
            raise RuntimeError('Cannot copy remote[{}] '
                               'to local[{}] with cmd[{}] '
                               'on error[{}]'.format(from_uri, local_path, cmd,
                                                     repr(e)))

    @staticmethod
    def copy_hdfs_to_hdfs(from_uri, to_uri):
        if from_uri.split(':')[0].strip() != to_uri.split(':')[0].strip():
            raise RuntimeError('from_uri[{}] takes with different prefix '
                               'compared to to_uri[{}]'.format(
                                   from_uri, to_uri))

        hadoop_bin = HDFS._hadoop_bin(from_uri)
        cmd = '{hbin} fs -cp {furi} {turi}'.format(hbin=hadoop_bin,
                                                   furi=from_uri,
                                                   turi=to_uri)
        try:
            ret, out = run_cmd_with_output(cmd)
            if ret == 0:
                return True
            elif ret == 1:
                return False
            else:
                raise RuntimeError('Cannot copy from_uri[{}] to '
                                   'to_uri[{}] with cmd[{}]; '
                                   'ret[{}] output[{}]'.format(
                                       from_uri, to_uri, cmd, ret, out))
        except Exception as e:
            raise RuntimeError('Cannot copy from_uri[{}] to '
                               'to_uri[{}] with cmd[{}] '
                               'on unexpected error[{}]'.format(
                                   from_uri, to_uri, cmd, repr(e)))

    @staticmethod
    def _hadoop_bin(uri):
        '''Choose hadoop client by uri
        Returns: path on success
        Raises: RuntimeError
        '''
        HDFS_CONFIG = {'hdfs': 'hadoop/bin/hadoop'}
        prefix = uri.split(':')[0].strip()
        if prefix in HDFS_CONFIG:
            return HDFS_CONFIG[prefix]
        else:
            raise RuntimeError('hdfs prefix[{}] has not '
                               'been registered'.format(prefix))
