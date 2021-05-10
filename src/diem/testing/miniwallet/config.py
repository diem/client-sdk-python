# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Tuple
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
    disable_events_api: bool = field(default=False)
    account_config: Dict[str, Any] = field(default_factory=lambda: LocalAccount().to_dict())
    child_account_configs: List[Dict[str, Any]] = field(default_factory=list)
    server_conf: ServerConfig = field(default_factory=ServerConfig)
    initial_amount: int = field(default=3_000_000_000_000)
    initial_currency: str = field(default=testnet.TEST_CURRENCY_CODE)
    child_account_size: int = field(default=2)

    @property
    def logger(self) -> logging.Logger:
        return logging.getLogger(self.name)

    @property
    def account(self) -> LocalAccount:
        return LocalAccount.from_dict(self.account_config)

    @property
    def child_accounts(self) -> List[LocalAccount]:
        return list(map(LocalAccount.from_dict, self.child_account_configs))

    @property
    def server_url(self) -> str:
        return self.server_conf.base_url

    def create_client(self) -> RestClient:
        self.logger.info("Creating client pointing to %s", self.server_url)
        return RestClient(server_url=self.server_url, name="%s-client" % self.name).with_retry()

    def setup_account(self, client: jsonrpc.Client) -> None:
        self.logger.info("faucet: mint %s", self.account.account_address.to_hex())
        faucet = testnet.Faucet(client)
        faucet.mint(self.account.auth_key.hex(), self.initial_amount, self.initial_currency)

        self.logger.info("rotate dual attestation info for %s", self.account.account_address.to_hex())
        self.logger.info("set base url to: %s", self.server_url)
        self.account.rotate_dual_attestation_info(client, self.server_url)

        self.logger.info("generate child VASP accounts: %s", self.child_account_size)
        child_account_initial_amount = int(self.initial_amount / (self.child_account_size + 1))
        for i in range(self.child_account_size):
            child = self.account.gen_child_vasp(client, child_account_initial_amount, self.initial_currency)
            self.logger.info("generate child VASP account(%s): %s", i, child.to_dict())
            self.child_account_configs.append(child.to_dict())

    def serve(self, client: jsonrpc.Client, app: App) -> threading.Thread:
        api: falcon.API = falcon_api(app, self.disable_events_api)

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

    def start(self, client: jsonrpc.Client) -> Tuple[App, threading.Thread]:
        self.setup_account(client)
        app = App(self.account, self.child_accounts, client, self.name, self.logger)
        t = self.serve(client, app)
        utils.wait_for_port(self.server_conf.port, host=self.server_conf.host)
        return (app, t)

    def __str__(self) -> str:
        return json.dumps(asdict(self), indent=2)
