"""Fake version of Archive Ingest.  Read from TCP port and pretend to
store store a FITS file in the archive"""

import asyncio

@asyncio.coroutine
def handle_ingest_request(reader, writer):
    data = yield from reader.read(100)
    message = data.decode()
    addr = writer.get_extra_info('peername')
    print("Received %r from %r" % (message, addr))

    print("Send: %r" % message)
    writer.write(data)
    yield from writer.drain()

    print("Close the client socket")
    writer.close()

def startup(host='127.0.0.1',port=8888):
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(handle_ingest_request, host, port, loop=loop)
    server = loop.run_until_complete(coro)

    # Serve requests until CTRL+c is pressed
    print('Serving on {}'.format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

   # Close the server
   server.close()
   loop.run_until_complete(server.wait_closed())
   loop.close() 
