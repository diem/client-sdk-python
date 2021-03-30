# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field, asdict
from typing import Dict, Any
from .client import RestClient
from .app import App, falcon_api
from .. import LocalAccount
from ... import offchain, testnet, jsonrpc, utils
import waitress, threading, logging, falcon, json


@dataclass
class ServerConfig:
    host: str = field(default="localhost")
    port: int = field(default_factory=offchain.http_server.get_available_port)
    base_url: str = field(default="")

    def __post_init__(self) -> None:
        if not self.base_url:
            self.base_url = f"http://localhost:{self.port}"


@dataclass
class AppConfig:
    name: str = field(default="mini-wallet")
    enable_debug_api: bool = field(default=False)
    account_config: Dict[str, Any] = field(default_factory=lambda: LocalAccount().to_dict())
    server_conf: ServerConfig = field(default_factory=ServerConfig)
    initial_amount: int = field(default=1_000_000_000_000)
    initial_currency: str = field(default=testnet.TEST_CURRENCY_CODE)

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.name)

    @property
    def account(self) -> LocalAccount:
        return LocalAccount.from_dict(self.account_config)

    @property
    def server_url(self) -> str:
        return self.server_conf.base_url

    def create_client(self) -> RestClient:
        self.logger.info("Creating client pointing to %s", self.server_url)
        return RestClient(server_url=self.server_url, name="%s-client" % self.name).with_retry()

    def setup_account(self, client: jsonrpc.Client) -> None:
        acc = client.get_account(self.account.account_address)
        if not acc or self.need_funds(acc):
            self.logger.info("faucet mint %s", self.account.account_address.to_hex())
            faucet = testnet.Faucet(client)
            faucet.mint(self.account.auth_key.hex(), self.initial_amount, self.initial_currency)
        if not acc or self.need_rotate(acc):
            self.logger.info("rotate dual attestation info for %s", self.account.account_address.to_hex())
            self.logger.info("set base url to: %s", self.server_url)
            self.account.rotate_dual_attestation_info(client, self.server_url)

    def need_funds(self, account: jsonrpc.Account) -> bool:
        for balance in account.balances:
            if balance.currency == self.initial_currency and balance.amount > self.initial_amount / 2:
                return False
        return True

    def need_rotate(self, account: jsonrpc.Account) -> bool:
        if account.role.base_url != self.server_url:
            return True
        if not account.role.compliance_key:
            return True
        if bytes.fromhex(account.role.compliance_key) != self.account.compliance_public_key_bytes:
            return True
        return False

    def serve(self, client: jsonrpc.Client) -> threading.Thread:
        api: falcon.API = falcon_api(App(self.account, client, self.name, self.logger), self.enable_debug_api)

        def serve() -> None:
            self.logger.info("serving on %s:%s at %s", self.server_conf.host, self.server_conf.port, self.server_url)
            waitress.serve(
                api,
                host=self.server_conf.host,
                port=self.server_conf.port,
                clear_untrusted_proxy_headers=True,
                _quiet=True,
            )

        t = threading.Thread(target=serve, daemon=True)
        t.start()
        return t

    def start(self, client: jsonrpc.Client) -> threading.Thread:
        self.setup_account(client)
        t = self.serve(client)
        utils.wait_for_port(self.server_conf.port, host=self.server_conf.host)
        return t

    def __str__(self) -> str:
        return json.dumps(asdict(self), indent=2)
