# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from click.testing import CliRunner, Result
from diem.testing import cli
from diem.testing.suites import envs
from diem.testing.miniwallet import ServerConfig, RestClient
from diem.testing import LocalAccount
from diem import identifier, testnet, utils
from typing import List
import json, threading, pytest, pkg_resources, time


@pytest.fixture(autouse=True)
def disable_self_check(monkeypatch) -> None:
    monkeypatch.delenv(envs.SELF_CHECK)


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_version(runner: CliRunner) -> None:
    version = pkg_resources.require("diem")[0].version

    for version_opt in ["-v", "--version"]:
        result = runner.invoke(cli.main, [version_opt])
        assert result.exit_code == 0
        assert ("version %s" % version) in result.output


def test_help_shortcut(runner: CliRunner) -> None:
    for fn in [cli.main, cli.start_server, cli.test, cli.gen_diem_account_config]:
        result = runner.invoke(fn, ["-h"])
        assert result.exit_code == 0
        assert ("-h, --help") in result.output


def test_gen_diem_account_config(runner: CliRunner) -> None:
    result = runner.invoke(cli.gen_diem_account_config, [])

    assert result.exit_code == 0

    account = LocalAccount.from_dict(json.loads(result.output))
    assert account.private_key
    assert account.compliance_key
    default = LocalAccount()
    default.private_key = account.private_key
    default.compliance_key = account.compliance_key
    assert default == account


def test_start_server_and_run_test_with_matching_keywords(runner: CliRunner) -> None:
    conf = start_target_server(runner)
    result = start_test(
        runner,
        conf,
        [
            "-k",
            "test_invalid_jws_message_signature or test_receive_payment_with_general_metadata_and_valid_from_and_to_subaddresses",
        ],
    )
    assert result.exit_code == 0, result.output


def test_run_test_with_pytest_args(runner: CliRunner) -> None:
    conf = start_target_server(runner)
    result = start_test(
        runner,
        conf,
        [
            "--pytest-args",
            "-k 'test_invalid_jws_message_signature or test_receive_payment_with_general_metadata_and_valid_from_and_to_subaddresses'",
        ],
    )
    assert result.exit_code == 0, result.output


def test_run_disable_offchainv2_tests_by_default(runner: CliRunner) -> None:
    conf = start_target_server(runner)
    result = start_test(
        runner,
        conf,
        [
            "--pytest-args",
            "-k 'test_invalid_x_request_id'",
        ],
    )
    assert result.exit_code == pytest.ExitCode.NO_TESTS_COLLECTED, result.output


def test_include_offchainv2_tests(runner: CliRunner) -> None:
    conf = start_target_server(runner)
    result = start_test(
        runner,
        conf,
        [
            "--include-offchain-v2",
            "--pytest-args",
            "-k 'test_invalid_x_request_id'",
        ],
    )
    assert result.exit_code == 0, result.output


def test_load_diem_account_config_file(runner: CliRunner) -> None:
    app_config_file = "app.json"
    stub_config_file = "stub.json"
    with runner.isolated_filesystem():
        LocalAccount(hrp=identifier.DM).write_to_file(app_config_file)
        LocalAccount(hrp=identifier.DM).write_to_file(stub_config_file)

        conf = start_target_server(runner, ["-i", app_config_file])
        result = start_test(
            runner,
            conf,
            [
                "-i",
                stub_config_file,
                "-k",
                "test_receive_payment_with_general_metadata_and_valid_from_and_to_subaddresses",
            ],
        )

        assert result.exit_code == 0, result.output

        # use the same configuration file for multiple times testing
        result = start_test(
            runner,
            conf,
            [
                "-i",
                stub_config_file,
                "-k",
                "test_send_payment_with_valid_inputs_under_the_travel_rule_threshold",
            ],
        )

        assert result.exit_code == 0, result.output


def test_hrp_option(runner: CliRunner) -> None:
    conf = start_target_server(runner, ["--hrp", "xdm"])
    c = RestClient(server_url=conf.base_url, name="test-hrp-option").with_retry()
    assert c.create_account().generate_account_identifier()[:3] == "xdm"

    result = start_test(
        runner,
        conf,
        [
            "--stub-hrp",
            "xdm",
            "-k",
            "test_generate_account_identifier",
        ],
    )
    assert result.exit_code == 0, result.output


def test_hrp_option_overwrites_hrp_from_diem_account_config_file(runner: CliRunner) -> None:
    app_config_file = "app.json"
    stub_config_file = "stub.json"
    with runner.isolated_filesystem():
        LocalAccount(hrp=identifier.DM).write_to_file(app_config_file)
        LocalAccount(hrp=identifier.DM).write_to_file(stub_config_file)

        conf = start_target_server(runner, ["-i", app_config_file, "--hrp", "xdm"])
        c = RestClient(server_url=conf.base_url, name="x").with_retry()
        assert c.create_account().generate_account_identifier()[:3] == "xdm"

        result = start_test(
            runner,
            conf,
            [
                "-i",
                stub_config_file,
                "--stub-hrp",
                "xdm",
                "-k",
                "test_generate_account_identifier",
            ],
        )

        assert result.exit_code == 0, result.output


def test_wait_timeout_for_target_ready(runner: CliRunner) -> None:
    start = time.time()
    result = start_test(
        runner,
        ServerConfig(),
        [
            "--wait-for-target-timeout",
            1,
            "-k",
            "test_create_a_blank_account",
        ],
    )
    assert result.exit_code == 1, result.output
    duration = time.time() - start
    assert duration < 2


# def test_cli_init_with_diem_id_domain(runner: CliRunner) -> None:
#     app_config_file = "app.json"
#     stub_config_file = "stub.json"
#     with runner.isolated_filesystem():
#         LocalAccount().write_to_file(app_config_file)
#         LocalAccount().write_to_file(stub_config_file)
#
#         conf = start_target_server(runner, ["-i", app_config_file, "--diem-id-domain", "targetdomain"])
#         result = start_test(
#             runner,
#             conf,
#             [
#                 "-i",
#                 stub_config_file,
#                 "-k",
#                 "test_create_a_blank_account",
#                 "--stub-diem-id-domain",
#                 "stubdomain",
#             ],
#         )
#
#         assert result.exit_code == 0, result.output


# def test_vasp_has_domain(stub_client: RestClient, target_client: RestClient, hrp: str) -> None:
#     """
#     Test Plan:
#
#     1. Generate a valid account identifier from receiver account as payee.
#     2. Send a payment to the account identifier.
#     3. Wait for the transaction executed successfully.
#     4. Assert receiver account received the fund.
#
#     """
#
#     sender_account = stub_client.create_account()
#     receiver_account = target_client.create_account()
#     account = target_client.create_account()
#     account_identifier = account.generate_account_identifier()
#     account_address, _ = identifier.decode_account(account_identifier, hrp)
#     assert account_address
#
#     client = testnet.create_client()
#     account = client.get_account(account_address)

# try:
#     payee = receiver_account.generate_account_identifier()
#     pay = sender_account.send_payment(currency=currency, amount=amount, payee=payee)
#     wait_for_payment_transaction_complete(sender_account, pay.id)
#     wait_for_balance(receiver_account, currency, amount)
# finally:
#     receiver_account.log_events()
#     sender_account.log_events()


def start_test(runner: CliRunner, conf: ServerConfig, options: List[str] = []) -> Result:
    stub_conf = ServerConfig()
    return runner.invoke(
        cli.test,
        [
            "--target",
            conf.base_url,
            "--jsonrpc",
            testnet.JSON_RPC_URL,
            "--faucet",
            testnet.FAUCET_URL,
            "--stub-bind-host",
            "0.0.0.0",
            "--stub-bind-port",
            stub_conf.port,
            "--stub-diem-account-base-url",
            stub_conf.base_url,
        ]
        + options,
    )


def start_target_server(runner: CliRunner, options: List[str] = []) -> ServerConfig:
    conf = ServerConfig(host="0.0.0.0")
    conf.base_url = "http://127.0.0.1:%s" % conf.port

    def start_server():
        runner.invoke(
            cli.start_server,
            [
                "--jsonrpc",
                testnet.JSON_RPC_URL,
                "--faucet",
                testnet.FAUCET_URL,
                "--host",
                conf.host,
                "--port",
                conf.port,
                "--diem-account-base-url",
                conf.base_url,
            ]
            + options,
        )

    threading.Thread(target=start_server, daemon=True).start()
    utils.wait_for_port(conf.port)
    return conf
