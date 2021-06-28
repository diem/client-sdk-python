# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from aiohttp import web
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from .client import RestClient
from .app import App, web_api
from .. import LocalAccount
from ... import testnet, jsonrpc, utils
import logging, json, asyncio


@dataclass
class ServerConfig:
    host: str = field(default="localhost")
    port: int = field(default_factory=utils.get_available_port)
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
    diem_id_domain: Optional[str] = field(default=None)

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
        return RestClient(server_url=self.server_url, name="%s-client" % self.name)

    async def setup_account(self, client: jsonrpc.Client) -> None:
        self.logger.info("faucet: mint %s", self.account.account_address.to_hex())
        faucet = testnet.Faucet(client)
        account = await client.get_account(self.account.account_address)
        domain = None if account and self.diem_id_domain in account.role.diem_id_domains else self.diem_id_domain
        await faucet.mint(
            self.account.auth_key.hex(), self.initial_amount, self.initial_currency, diem_id_domain=domain
        )

        self.logger.info("rotate dual attestation info for %s", self.account.account_address.to_hex())
        self.logger.info("set base url to: %s", self.server_url)
        await self.account.rotate_dual_attestation_info(client, self.server_url)

        self.logger.info("generate child VASP accounts: %s", self.child_account_size)
        child_account_initial_amount = int(self.initial_amount / (self.child_account_size + 1))
        for i in range(self.child_account_size):
            child = await self.account.gen_child_vasp(client, child_account_initial_amount, self.initial_currency)
            self.logger.info("generate child VASP account(%s): %s", i, child.to_dict())
            self.child_account_configs.append(child.to_dict())

    async def serve(self, client: jsonrpc.Client, app: App, blocking: bool) -> None:
        self.logger.info("serving on %s:%s at %s", self.server_conf.host, self.server_conf.port, self.server_url)
        api = await web_api(app, self.disable_events_api)

        runner = web.AppRunner(api)
        await runner.setup()
        site = web.TCPSite(runner, self.server_conf.host, self.server_conf.port)
        await site.start()
        if blocking:
            while True:
                await asyncio.sleep(1)

    async def start(self, client: jsonrpc.Client, blocking: bool = False) -> App:
        await self.setup_account(client)
        app = App(self.account, self.child_accounts, client, self.name, self.logger)
        await self.serve(client, app, blocking)
        await utils.wait_for_port(self.server_conf.port, host=self.server_conf.host)
        return app

    def __str__(self) -> str:
        return json.dumps(asdict(self), indent=2)
