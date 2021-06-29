# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, asdict, field
from typing import Any
from .app import App
from .offchain_api_v2 import OffChainAPIv2
from .json_input import JsonInput
from .... import offchain
import json, traceback, pathlib
from aiohttp import web


base_path: str = str(pathlib.Path(__file__).resolve().parent.joinpath("static"))


def rest_handler(fn: Any):  # pyre-ignore
    async def wrapper(endpoints: "Endpoints", req: web.Request) -> web.Response:
        try:
            if req.content_length:
                try:
                    data = json.loads(await req.text())
                except json.decoder.JSONDecodeError:
                    raise ValueError("request body is invalid JSON")
                endpoints.app.logger.debug("request body: %s", data)
            else:
                data = {}
            account_id = req.match_info.get("account_id")
            kwargs = {"account_id": account_id} if account_id else {}
            return await fn(endpoints, input=JsonInput(data), **kwargs)
        except ValueError as e:
            body = {"error": str(e), "stacktrace": traceback.format_exc()}
            return web.json_response(body, status=400)

    return wrapper


@dataclass
class Endpoints:
    app: App
    offchain_api_v2: OffChainAPIv2 = field(init=False)

    def __post_init__(self) -> None:
        self.offchain_api_v2 = OffChainAPIv2(self.app)
        self.app.add_bg_task(self.offchain_api_v2._process_offchain_commands)
        self.app.add_dual_attestation_txn_sender("v2", self.offchain_api_v2.send_dual_attestation_transaction)

    @rest_handler
    async def accounts(self, input: JsonInput) -> web.Response:
        return web.json_response(await self.app.create_account(input), status=201)

    @rest_handler
    async def account_payments(self, input: JsonInput, account_id: str) -> web.Response:
        ret = await self.app.create_account_payment(account_id, input)
        return web.json_response(ret, status=202)

    @rest_handler
    async def account_identifiers(self, input: JsonInput, account_id: str) -> web.Response:
        return web.json_response(self.app.create_account_identifier(account_id, input))

    @rest_handler
    async def account_balances(self, account_id: str, input: JsonInput) -> web.Response:
        return web.json_response(self.app.get_account_balances(account_id))

    @rest_handler
    async def account_events(self, account_id: str, input: JsonInput) -> web.Response:
        return web.json_response([asdict(e) for e in self.app.get_account_events(account_id)])

    @rest_handler
    async def kyc_sample(self, input: JsonInput) -> web.Response:
        return web.json_response(asdict(self.app.kyc_sample))

    async def offchain_v2(self, req: web.Request) -> web.Response:
        request_id = req.headers.get(offchain.X_REQUEST_ID, "")
        request_sender_address = req.headers.get(offchain.X_REQUEST_SENDER_ADDRESS, "")
        input_data = await req.read()

        resp_obj = await self.offchain_api_v2.process(request_id, request_sender_address, input_data)
        body = self.offchain_api_v2.jws_serialize(resp_obj)
        status = 400 if resp_obj.error is not None else 200
        headers = {offchain.X_REQUEST_ID: request_id}
        return web.Response(body=body, status=status, headers=headers)


async def root_handler(request: web.Request) -> web.Response:
    return web.HTTPFound("/index.html")


async def web_api(app: App, disable_events_api: bool = False) -> web.Application:
    endpoints = Endpoints(app=app)

    api = web.Application()
    api.router.add_route("get", "/", root_handler)

    api.router.add_route("post", "/accounts", endpoints.accounts)
    api.router.add_route("get", "/accounts/{account_id}/balances", endpoints.account_balances)
    api.router.add_route("post", "/accounts/{account_id}/account_identifiers", endpoints.account_identifiers)
    api.router.add_route("post", "/accounts/{account_id}/payments", endpoints.account_payments)
    api.router.add_route("get", "/kyc_sample", endpoints.kyc_sample)
    api.router.add_route("post", "/v2/command", endpoints.offchain_v2)
    if not disable_events_api:
        api.router.add_route("get", "/accounts/{account_id}/events", endpoints.account_events)

    api.router.add_static("/", base_path)

    async def on_startup(ap: web.Application) -> None:
        ap["worker"] = await app.start_worker()

    async def on_cleanup(ap: web.Application) -> None:
        ap["worker"].cancel()
        await ap["worker"]

    api.on_startup.append(on_startup)
    api.on_cleanup.append(on_cleanup)

    return api
