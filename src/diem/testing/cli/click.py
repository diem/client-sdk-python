# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from diem import testnet
from diem.testing.miniwallet import AppConfig, ServerConfig
from diem.testing.suites import envs
from typing import Optional
import logging, click, functools, pytest, os, sys, re

log_format: str = "%(name)s [%(asctime)s] %(levelname)s: %(message)s"
click.option = functools.partial(click.option, show_default=True)  # pyre-ignore


@click.group()
def main() -> None:
    pass


@click.command()
@click.option("--name", "-n", default="mini-wallet", help="Application name.")
@click.option("--host", "-h", default="localhost", help="Start server host.")
@click.option("--port", "-p", default=8888, help="Start server port.")
@click.option("--jsonrpc", "-j", default=testnet.JSON_RPC_URL, help="Diem fullnode JSON-RPC URL.")
@click.option("--faucet", "-f", default=testnet.FAUCET_URL, help="Testnet faucet URL.")
@click.option("--logfile", "-l", default=None, help="Log to a file instead of printing into console.")
@click.option("--enable-debug-api", "-o", default=True, help="Enable debug API.", type=bool, is_flag=True)
def start_server(
    name: str, host: str, port: int, jsonrpc: str, faucet: str, enable_debug_api: bool, logfile: Optional[str] = None
) -> None:
    logging.basicConfig(level=logging.INFO, format=log_format, filename=logfile)
    configure_testnet(jsonrpc, faucet)

    conf = AppConfig(name=name, server_conf=ServerConfig(host=host, port=port), enable_debug_api=enable_debug_api)
    print("Server Config: %s" % conf)

    client = testnet.create_client()
    print("Diem chain id: %s" % client.get_metadata().chain_id)

    conf.start(client).join()


@click.command()
@click.option("--target", "-t", default="http://localhost:8888", help="Target mini-wallet application URL.")
@click.option("--stub-bind-host", "-h", default="localhost", help="The host the miniwallet stub server will bind to")
@click.option(
    "--stub-bind-port",
    "-p",
    default=None,
    help="The port the miniwallet stub server will bind to. Random if empty.",
    type=int,
)
@click.option(
    "--stub-diem-account-base-url",
    "-u",
    default=None,
    help="The address that will be used for offchain callbacks. Defaults to http://localhost:{random_port}",
)
@click.option("--jsonrpc", "-j", default=testnet.JSON_RPC_URL, help="Diem fullnode JSON-RPC URL.")
@click.option("--faucet", "-f", default=testnet.FAUCET_URL, help="Testnet faucet URL.")
@click.option(
    "--pytest-args",
    default="",
    help="Additional pytest arguments, split by empty space, e.g. `--pytest-args '-v -s'`.",
    show_default=False,
)
@click.option("--test-debug-api", "-d", default=False, help="Run tests for debug APIs.", type=bool)
@click.option("--verbose", "-v", default=False, help="Enable verbose log output.", type=bool, is_flag=True)
def test(
    target: str,
    stub_bind_host: Optional[str],
    stub_bind_port: Optional[int],
    stub_diem_account_base_url: Optional[str],
    jsonrpc: str,
    faucet: str,
    pytest_args: str,
    test_debug_api: bool,
    verbose: bool,
) -> None:
    configure_testnet(jsonrpc, faucet)
    os.environ[envs.TARGET_URL] = target

    # If stub_bind_host is provided, then stub_diem_account_base_url must be as well or the test won't work
    if stub_bind_host is not None and stub_bind_host != "localhost" and not stub_diem_account_base_url:
        raise click.ClickException("--stub-diem-account-base-url is required when passing in a custom --stub-bind-host")

    if stub_bind_host:
        os.environ[envs.DMW_STUB_BIND_HOST] = str(stub_bind_host)
    if stub_bind_port:
        os.environ[envs.DMW_STUB_BIND_PORT] = str(stub_bind_port)
    if stub_diem_account_base_url:
        os.environ[envs.DMW_STUB_DIEM_ACCOUNT_BASE_URL] = stub_diem_account_base_url

    if test_debug_api:
        os.environ[envs.TEST_DEBUG_API] = "Y"

    args = [arg for arg in re.compile("\\s+").split(pytest_args) if arg]
    args = ["--pyargs", "diem.testing.suites"] + args
    if verbose:
        args.append("--log-level=INFO")
        args.append("-s")
        args.append("-v")

    code = pytest.main(args)
    sys.stdout.flush()
    raise SystemExit(code)


def configure_testnet(jsonrpc: str, faucet: str) -> None:
    testnet.JSON_RPC_URL = jsonrpc
    testnet.FAUCET_URL = faucet
    print("Diem JSON-RPC URL: %s" % testnet.JSON_RPC_URL)
    print("Diem Testnet Faucet URL: %s" % testnet.FAUCET_URL)


main.add_command(start_server)
main.add_command(test)
