
import time
import json
import asyncio
from importlib import resources
from js import WebSocket
from .crypto import address_to_scripthash


class ElectrumClient:
    def __init__(self, servers_file="servers.json"):
        self.url = None
        self.ws = None

        self._id = 0
        self._pending = {}
        self.on_notification = None
        self.on_status = None
        self._keepalive_task = None

        with resources.files("btczpy").joinpath(servers_file).open("r") as f:
            self.servers = json.load(f)

        self._loop = asyncio.get_event_loop()


    async def keepalive(self, interval=30):
        while True:
            try:
                await self.ping()
            except Exception as e:
                pass
            await asyncio.sleep(interval)


    async def _measure_server(self, url, timeout=5):
        start = time.perf_counter()
        try:
            ws = WebSocket.new(url)
            future = self._loop.create_future()
            def on_open(event):
                if not future.done():
                    latency = (time.perf_counter() - start) * 1000
                    future.set_result(latency)
            def on_error(event):
                if not future.done():
                    future.set_exception(Exception("Connection failed"))

            ws.onopen = on_open
            ws.onerror = on_error
            latency = await asyncio.wait_for(future, timeout=timeout)
            ws.close()
            return (url, latency)
        except:
            return (url, float("inf"))


    async def get_fastest_server(self):
        tasks = [
            self._measure_server(url)
            for url in self.servers
        ]
        results = await asyncio.gather(*tasks)
        results.sort(key=lambda x: x[1])
        fastest_url, latency = results[0]
        if latency == float("inf"):
            raise Exception("No available servers")

        return fastest_url


    async def connect(self):
        self.url = await self.get_fastest_server()
        if self.on_status:
            self.on_status("connecting")
        self.ws = WebSocket.new(self.url)
        future = self._loop.create_future()
        def on_open(event):
            future.set_result(True)
            if self.on_status:
                self.on_status("connected")
        def on_error(event):
            if not future.done():
                future.set_exception(Exception("WebSocket connection failed"))
        def on_message(event):
            self._handle_message(event.data)
        async def reconnect_task():
            await self.reconnect()
        def on_close(event):
            if self.on_status:
                self.on_status("disconnected")
            self._loop.create_task(reconnect_task())
        self.ws.onopen = on_open
        self.ws.onerror = on_error
        self.ws.onmessage = on_message
        self.ws.onclose = on_close
        await future
        if not self._keepalive_task or self._keepalive_task.done():
            self._keepalive_task = self._loop.create_task(self.keepalive())


    async def reconnect(self):
        if self.on_status:
            self.on_status("reconnecting")
        self.close()
        await asyncio.sleep(2)
        await self.connect()


    def close(self):
        if self.ws:
            self.ws.close()
            self.ws = None

        for future in self._pending.values():
            if not future.done():
                future.set_exception(Exception("Connection closed"))
        self._pending.clear()


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
    
    async def get_fee_histogram(self):
        return await self.send("mempool.get_fee_histogram")

    async def get_relay_fee(self):
        return await self.send("blockchain.relayfee")

    async def get_donation_address(self):
        return await self.send("server.donation_address")
    
    async def server_version(self, client_name="Electrum Web Wallet", protocol_version="1.4"):
        return await self.send("server.version", [client_name, protocol_version])
    
    async def ping(self):
        return await self.send("server.ping")