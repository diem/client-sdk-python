# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

"""This module provides command-line interface for starting mini-wallet application and running test suites.
"""

from diem import utils
from diem.testing import LocalAccount, create_client, JSON_RPC_URL, FAUCET_URL
from diem.testing.miniwallet import AppConfig, ServerConfig
from diem.testing.suites import envs
from typing import Optional, TextIO
from urllib.parse import urlsplit
import logging, click, functools, pytest, os, sys, json, shlex, asyncio


log_format: str = "%(name)s [%(asctime)s] %(levelname)s: %(message)s"
click.option = functools.partial(click.option, show_default=True)


def coro(f):  # pyre-ignore
    @functools.wraps(f)
    def wrapper(*args, **kwargs):  # pyre-ignore
        return asyncio.run(f(*args, **kwargs))

    return wrapper


def set_env(name: str, is_io: bool = False):  # pyre-ignore
    def callback(_c, _p, val):  # pyre-ignore
        if val:
            val = val.read() if is_io else str(val)
            os.environ[name] = val
            print("%s: %s" % (name, val))

        return val

    return callback


@click.group()
@click.version_option(None, "-v", "--version")
@click.help_option("-h", "--help")
def main() -> None:
    pass


@click.command()
@click.option("--name", "-n", default="mini-wallet", help="Application name.")
@click.option("--host", "-H", default="localhost", help="Start server host.")
@click.option("--port", "-p", default=8888, help="Start server port.")
@click.option(
    "--diem-account-base-url",
    "-u",
    default=None,
    help="The address that will be used for offchain callbacks. Defaults to http://localhost:{port}",
)
@click.option(
    "--jsonrpc", "-j", default=JSON_RPC_URL, callback=set_env("DIEM_JSON_RPC_URL"), help="Diem fullnode JSON-RPC URL."
)
# pyre-ignore
@click.option("--faucet", "-f", default=FAUCET_URL, callback=set_env("DIEM_FAUCET_URL"), help="Testnet faucet URL.")
@click.option("--disable-events-api", "-o", default=False, help="Disable account events API.", type=bool, is_flag=True)
@click.option(
    "--logfile", "-l", default=None, type=click.Path(), help="Log to a file instead of printing into console."
)
@click.option(
    "--import-diem-account-config-file",
    "-i",
    default=None,
    help="Import the diem account config from a file. The config file content should be JSON generated from command `gen-diem-account-config`.",
    type=click.File(),
)
@click.option(
    "--hrp",
    default=None,
    help="Set Diem account identifier hrp; if '-i' option is used, this option overwrites hrp configured by '-i' option.",
    type=str,
)
@click.help_option("-h", "--help")
@coro
async def start_server(
    name: str,
    host: str,
    port: int,
    diem_account_base_url: Optional[str],
    jsonrpc: str,
    faucet: str,
    disable_events_api: bool,
    import_diem_account_config_file: Optional[TextIO],
    logfile: Optional[str],
    hrp: str,
) -> None:
    logging.basicConfig(level=logging.INFO, format=log_format, filename=logfile)

    conf = AppConfig(
        name=name,
        server_conf=ServerConfig(host=host, port=port, base_url=diem_account_base_url or ""),
        disable_events_api=disable_events_api,
    )
    if import_diem_account_config_file:
        conf.account_config = json.load(import_diem_account_config_file)
    if hrp:
        conf.account_config["hrp"] = hrp

    print("Server Config: %s" % conf)

    client = create_client()
    metadata = await client.get_metadata()
    print("Diem chain id: %s" % metadata.chain_id)

    _, runner = await conf.start(client)
    try:
        while True:
            await asyncio.sleep(3600)
    finally:
        await runner.cleanup()


@click.command()
@click.option(
    "--target",
    "-t",
    default="http://localhost:8888",
    callback=set_env(envs.TARGET_URL),
    help="Target mini-wallet application URL.",
)
@click.option(
    "--stub-bind-host",
    "-H",
    default="localhost",
    callback=set_env(envs.DMW_STUB_BIND_HOST),
    help="The host the miniwallet stub server will bind to",
)
@click.option(
    "--stub-bind-port",
    "-p",
    default=None,
    callback=set_env(envs.DMW_STUB_BIND_PORT),
    help="The port the miniwallet stub server will bind to. Random if empty.",
    type=int,
)
@click.option(
    "--stub-diem-account-base-url",
    "-u",
    default=None,
    callback=set_env(envs.DMW_STUB_DIEM_ACCOUNT_BASE_URL),
    help="The address that will be used for offchain callbacks. Defaults to http://localhost:{port}",
)
@click.option(
    "--jsonrpc", "-j", default=JSON_RPC_URL, callback=set_env("DIEM_JSON_RPC_URL"), help="Diem fullnode JSON-RPC URL."
)
@click.option(
    "--match-keywords",
    "-k",
    default=None,
    help="Only run tests which match the given substring expression. Same with pytest `-k` option. Example: -k 'test_method or test_other' matches all test functions and classes whose name contains 'test_method' or 'test_other', while -k 'not test_method' matches those that don't contain 'test_method' in their names",
)
@click.option("--faucet", "-f", default=FAUCET_URL, callback=set_env("DIEM_FAUCET_URL"), help="Testnet faucet URL.")
@click.option(
    "--pytest-args",
    default="",
    help="Additional pytest arguments, split by empty space, e.g. `--pytest-args '-v -s'`.",
    show_default=False,
)
@click.option(
    "--logfile", "-l", default=None, help="Log to a file instead of printing into console.", type=click.Path()
)
@click.option("--verbose", "-v", default=False, help="Enable verbose log output.", type=bool, is_flag=True)
@click.option(
    "--import-stub-diem-account-config-file",
    "-i",
    default=None,
    callback=set_env(envs.DMW_STUB_DIEM_ACCOUNT_CONFIG, is_io=True),
    help="Import the diem account config from a file for the miniwallet stub server. The config file content should be JSON generated from command `gen-diem-account-config`.",
    type=click.File(),
)
@click.option(  # pyre-ignore
    "--stub-hrp",
    default=None,
    help="Set Diem account identifier hrp for the stub wallet application; if '-i' option is used, this option overwrites hrp configured by '-i' option.",
    type=str,
    callback=set_env(envs.DMW_STUB_DIEM_ACCOUNT_HRP),
)
@click.option(
    "--wait-for-target-timeout",
    default=20,
    help="Before start test, the target wallet application host port should be ready for connection. This is wait timeout (seconds) for the port ready.",
    type=int,
)
@click.option("--include-offchain-v2", type=bool, is_flag=True, default=False, help="Include offchain v2 test suites")
@click.help_option("-h", "--help")
def test(
    target: str,
    stub_bind_host: Optional[str],
    stub_bind_port: Optional[int],
    stub_diem_account_base_url: Optional[str],
    jsonrpc: str,
    match_keywords: str,
    faucet: str,
    pytest_args: str,
    logfile: Optional[str],
    verbose: bool,
    import_stub_diem_account_config_file: Optional[TextIO],
    stub_hrp: Optional[str],
    wait_for_target_timeout: int,
    include_offchain_v2: bool,
) -> None:
    # If stub_bind_host is provided, then stub_diem_account_base_url must be as well or the test won't work
    if stub_bind_host is not None and stub_bind_host != "localhost" and not stub_diem_account_base_url:
        raise click.ClickException("--stub-diem-account-base-url is required when passing in a custom --stub-bind-host")

    url = urlsplit(target)
    target_port = url.port or 80
    print("Waiting for %s:%s ready" % (url.hostname, target_port))
    utils.wait_for_port(target_port, host=str(url.hostname), timeout=wait_for_target_timeout)
    print("Target wallet at %s:%s is ready for connection" % (url.hostname, target_port))

    args = ["--pyargs", "diem.testing.suites.basic"]
    if include_offchain_v2:
        args.append("diem.testing.suites.offchainv2")
    args += shlex.split(pytest_args)
    if match_keywords:
        args.append("-k")
        args.append(match_keywords)
    if verbose:
        args.append("--log-level=INFO")
        args.append("-s")
        args.append("-v")
    if logfile:
        args.append("--log-file=%s" % logfile)

    code = pytest.main(args)
    sys.stdout.flush()
    raise SystemExit(code)


@click.command()
@click.help_option("-h", "--help")
def gen_diem_account_config() -> None:
    print(LocalAccount().to_json())


main.add_command(start_server)
main.add_command(test)
main.add_command(gen_diem_account_config)
