import argparse
from argparse import ArgumentTypeError, Namespace
import logging

import pytest

from unittest.mock import patch


@pytest.fixture
def reset_bigchaindb_config(monkeypatch):
    import bigchaindb
    monkeypatch.setattr('bigchaindb.config', bigchaindb._config)


def test_input_on_stderr():
    from bigchaindb.commands.utils import input_on_stderr, _convert

    with patch('builtins.input', return_value='I love cats'):
        assert input_on_stderr() == 'I love cats'

    # input_on_stderr uses `_convert` internally, from now on we will
    # just use that function

    assert _convert('hack the planet') == 'hack the planet'
    assert _convert('42') == '42'
    assert _convert('42', default=10) == 42
    assert _convert('', default=10) == 10
    assert _convert('42', convert=int) == 42
    assert _convert('True', convert=bool) is True
    assert _convert('False', convert=bool) is False
    assert _convert('t', convert=bool) is True
    assert _convert('3.14', default=1.0) == 3.14
    assert _convert('TrUe', default=False) is True

    with pytest.raises(ValueError):
        assert _convert('TRVE', default=False)

    with pytest.raises(ValueError):
        assert _convert('ಠ_ಠ', convert=int)


@pytest.mark.usefixtures('ignore_local_config_file', 'reset_bigchaindb_config')
def test_configure_bigchaindb_configures_bigchaindb():
    from bigchaindb.commands.utils import configure_bigchaindb
    from bigchaindb.config_utils import is_configured
    assert not is_configured()

    @configure_bigchaindb
    def test_configure(args):
        assert is_configured()

    args = Namespace(config=None)
    test_configure(args)


@pytest.mark.usefixtures('ignore_local_config_file',
                         'reset_bigchaindb_config',
                         'reset_logging_config')
@pytest.mark.parametrize('log_level', (
    logging.DEBUG,
    logging.INFO,
    logging.WARNING,
    logging.ERROR,
    logging.CRITICAL,
))
def test_configure_bigchaindb_logging(log_level):
    from bigchaindb.commands.utils import configure_bigchaindb
    from bigchaindb import config
    assert not config['log']

    @configure_bigchaindb
    def test_configure_logger(args):
        pass

    args = Namespace(config=None, log_level=log_level)
    test_configure_logger(args)
    from bigchaindb import config
    assert config['log']['level_console'] == log_level
    assert config['log']['level_logfile'] == log_level


def test_start_raises_if_command_not_implemented():
    from bigchaindb.commands import utils
    from bigchaindb.commands.bigchaindb import create_parser

    parser = create_parser()

    with pytest.raises(NotImplementedError):
        # Will raise because `scope`, the third parameter,
        # doesn't contain the function `run_start`
        utils.start(parser, ['start'], {})


def test_start_raises_if_no_arguments_given():
    from bigchaindb.commands import utils
    from bigchaindb.commands.bigchaindb import create_parser

    parser = create_parser()

    with pytest.raises(SystemExit):
        utils.start(parser, [], {})


@patch('multiprocessing.cpu_count', return_value=42)
def test_start_sets_multiprocess_var_based_on_cli_args(mock_cpu_count):
    from bigchaindb.commands import utils

    def run_mp_arg_test(args):
        return args

    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers(title='Commands',
                                      dest='command')
    mp_arg_test_parser = subparser.add_parser('mp_arg_test')
    mp_arg_test_parser.add_argument('-m', '--multiprocess',
                                    nargs='?',
                                    type=int,
                                    default=False)

    scope = {'run_mp_arg_test': run_mp_arg_test}
    assert utils.start(parser, ['mp_arg_test'], scope).multiprocess == 1
    assert utils.start(parser, ['mp_arg_test', '--multiprocess'], scope).multiprocess == 42


def test_mongodb_host_type():
    from bigchaindb.commands.utils import mongodb_host

    # bad port provided
    with pytest.raises(ArgumentTypeError):
        mongodb_host('localhost:11111111111')

    # no port information provided
    with pytest.raises(ArgumentTypeError):
        mongodb_host('localhost')

    # bad host provided
    with pytest.raises(ArgumentTypeError):
        mongodb_host(':27017')
