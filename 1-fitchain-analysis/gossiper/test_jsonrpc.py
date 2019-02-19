from aiohttp.web import Application
from aiohttp_json_rpc import JsonRpc
import asyncio


async def fit_sendTransaction(request):
    print('from fit_sendTransaction')
    return 'pong'


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    rpc = JsonRpc()
    rpc.add_methods(
        ('heloo', fit_sendTransaction),
    )

    app = Application(loop=loop)
    app.router.add_route('*', '/', rpc)

    handler = app.make_handler()

    print("Starting RPC server ")
    server = loop.run_until_complete(
        loop.create_server(handler, '0.0.0.0', 4000))

    loop.run_forever()
