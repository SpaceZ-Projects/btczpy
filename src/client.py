
import json
import asyncio
from js import WebSocket
from .crypto import address_to_scripthash


class ElectrumClient:
    def __init__(self, url="wss://electrum3.btcz.rocks:50004"):
        self.url = url
        self.ws = None

        self._id = 0
        self._pending = {}
        self.on_notification = None

        self._loop = asyncio.get_event_loop()


    async def connect(self):
        self.ws = WebSocket.new(self.url)
        future = self._loop.create_future()
        def on_open(event):
            future.set_result(True)
        def on_error(event):
            future.set_exception(Exception("WebSocket connection failed"))
        def on_message(event):
            self._handle_message(event.data)
        self.ws.onopen = on_open
        self.ws.onerror = on_error
        self.ws.onmessage = on_message
        await future


    def close(self):
        if self.ws:
            self.ws.close()
            self.ws = None


    def _handle_message(self, raw):
        msg = json.loads(raw)
        if "id" in msg:
            req_id = msg["id"]
            future = self._pending.pop(req_id, None)

            if future:
                if "error" in msg and msg["error"]:
                    future.set_exception(Exception(msg["error"]))
                else:
                    future.set_result(msg["result"])
        else:
            self._handle_notification(msg)


    def _handle_notification(self, msg):
        if self.on_notification:
            self.on_notification(msg)


    async def send(self, method, params=None):
        if params is None:
            params = []

        self._id += 1
        req_id = self._id
        request = {
            "jsonrpc": "2.0",
            "id": req_id,
            "method": method,
            "params": params
        }
        future = self._loop.create_future()
        self._pending[req_id] = future
        self.ws.send(json.dumps(request))
        return await future


    async def subscribe_headers(self):
        return await self.send("blockchain.headers.subscribe")

    async def unsubscribe_headers(self):
        return await self.send("blockchain.headers.unsubscribe")

    async def subscribe_address(self, address):
        sh = address_to_scripthash(address)
        return await self.send("blockchain.scripthash.subscribe", [sh])

    async def unsubscribe_address(self, address):
        sh = address_to_scripthash(address)
        return await self.send("blockchain.scripthash.unsubscribe", [sh])


    async def get_balance(self, address):
        sh = address_to_scripthash(address)
        return await self.send("blockchain.scripthash.get_balance", [sh])

    async def get_history(self, address):
        sh = address_to_scripthash(address)
        return await self.send("blockchain.scripthash.get_history", [sh])

    async def get_listunspent(self, address):
        sh = address_to_scripthash(address)
        return await self.send("blockchain.scripthash.listunspent", [sh])

    async def get_mempool(self, address):
        sh = address_to_scripthash(address)
        return await self.send("blockchain.scripthash.get_mempool", [sh])

    async def get_transaction(self, txid, verbose=True):
        return await self.send("blockchain.transaction.get", [txid, verbose])

    async def broadcast(self, tx_hex):
        return await self.send("blockchain.transaction.broadcast", [tx_hex])

    async def estimate_fee(self, blocks):
        return await self.send("blockchain.estimatefee", [blocks])

    async def get_relay_fee(self):
        return await self.send("blockchain.relayfee")

    async def get_donation_address(self):
        return await self.send("server.donation_address")