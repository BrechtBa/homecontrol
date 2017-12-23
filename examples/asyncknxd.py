import knxpy
import asyncio



def callback(data):
    message = knxpy.asyncknxd.default_callback(data)
    print(message)


connection = knxpy.asyncknxd.KNXD(ip='localhost', port=6720, callback=callback)

async def main():
    await connection.connect()
    print('connected')
        
    connection.group_write('1/1/61', 0)
    connection.group_write('1/1/61', 1)

    
loop = asyncio.get_event_loop()
loop.create_task(main())
loop.run_forever()

