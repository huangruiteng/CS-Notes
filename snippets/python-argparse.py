parser.add_argument("--hidden_dims", type=int, nargs='+', default=[1024, 1024], help="...")

nargs = '+'、'*'

from argparse import ArgumentParser, BooleanOptionalAction

parser = ArgumentParser()
parser.add_argument('--use_windowed_seq_profile', action=BooleanOptionalAction, default=False)
parser.add_argument('--flag_store_true', action='store_true', default=False)

CLI_USAGE_BOOLEAN = "--use_windowed_seq_profile / --no-use_windowed_seq_profile"
