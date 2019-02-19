import json
import logging
import aiohttp
import asyncio
import random

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


N_REQS = 100

payload = {
    "jsonrpc":"1.0",
    "method":"fit_sendTransaction",
    "params": [],
    "id": 42
}

rpc_addr  = '127.0.0.1'
rpc_ports = [4242, 4343, 4444]     # make sure nodes are running on these ports


async def create_tx(session, url):
    payload['params'] = [41, 42, 0.55] #params
    async with session.post(url, json=payload) as response:
        return await response.text()

async def main():
    # randomly choose a target node
    idx = random.randint(0, len(rpc_ports)-1)
    async with aiohttp.ClientSession() as session:        
        res = await create_tx(session,
                              'http://'+ rpc_addr + ':' + str(rpc_ports[idx]))
        print('back from request', res)

        
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(asyncio.gather(*[main() for i in range(N_REQS)]))
