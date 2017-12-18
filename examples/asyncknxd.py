import knxpy
import asyncio

def callback(data):
    message = knxpy.asyncknxd.default_callback(data)
    print(message)


connection = knxpy.asyncknxd.KNXD(ip='localhost', port=6720, callback=callback)

async def main():
    await connection.connect()

    
loop = asyncio.get_event_loop()
loop.run_until_complete(main())

