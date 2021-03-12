# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from click.testing import CliRunner, Result
from diem.testing.cli import click
from diem.testing.suites import envs
from diem.testing.miniwallet import ServerConfig
from diem import identifier, testnet, utils, LocalAccount
from typing import List
import json, threading, pytest


@pytest.fixture(autouse=True)
def disable_self_check(monkeypatch) -> None:
    monkeypatch.delenv(envs.SELF_CHECK)


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_gen_diem_account_config(runner: CliRunner) -> None:
    result = runner.invoke(click.gen_diem_account_config, [])

    assert result.exit_code == 0

    account = LocalAccount.from_dict(json.loads(result.output))
    assert account.private_key
    assert account.compliance_key
    default = LocalAccount()
    default.private_key = account.private_key
    default.compliance_key = account.compliance_key
    assert default == account


def test_start_server_and_run_one_test(runner: CliRunner) -> None:
    conf = start_target_server(runner)
    result = start_test(runner, conf)
    assert result.exit_code == 0, result.output


def test_load_diem_account_config_file(runner: CliRunner) -> None:
    app_config_file = "app.json"
    stub_config_file = "stub.json"
    with runner.isolated_filesystem():
        LocalAccount(hrp=identifier.DM).write_to_file(app_config_file)
        LocalAccount(hrp=identifier.DM).write_to_file(stub_config_file)

        conf = start_target_server(runner, ["-i", app_config_file])
        result = start_test(runner, conf, ["-i", stub_config_file])

        assert result.exit_code == 0, result.output


def start_test(runner: CliRunner, conf: ServerConfig, options: List[str] = []) -> Result:
    return runner.invoke(
        click.test,
        [
            "--target",
            conf.base_url,
            "--jsonrpc",
            testnet.JSON_RPC_URL,
            "--faucet",
            testnet.FAUCET_URL,
            "--pytest-args",
            "-k test_receive_payment_with_general_metadata_and_valid_from_and_to_subaddresses",
        ]
        + options,
    )


def start_target_server(runner: CliRunner, options: List[str] = []) -> ServerConfig:
    conf = ServerConfig()

    def start_server():
        runner.invoke(
            click.start_server,
            [
                "--jsonrpc",
                testnet.JSON_RPC_URL,
                "--faucet",
                testnet.FAUCET_URL,
                "--port",
                conf.port,
            ]
            + options,
        )

    threading.Thread(target=start_server, daemon=True).start()
    utils.wait_for_port(conf.port)
    return conf
