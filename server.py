# backend/server.py
import asyncio
import websockets
import json

connected_peers = {}

async def handler(websocket, path):
    peer_id = None
    try:
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "register":
                peer_id = data["peerId"]
                connected_peers[peer_id] = websocket
                await notify_peers()

            elif data["type"] in ("offer", "answer", "candidate"):
                target = data["to"]
                if target in connected_peers:
                    await connected_peers[target].send(message)

    except:
        pass
    finally:
        if peer_id in connected_peers:
            del connected_peers[peer_id]
            await notify_peers()

async def notify_peers():
    peer_list = list(connected_peers.keys())
    message = json.dumps({"type": "peer-list", "peers": peer_list})
    await asyncio.gather(*(ws.send(message) for ws in connected_peers.values()))

start_server = websockets.serve(handler, "0.0.0.0", 8765)
print("WebSocket server running on ws://localhost:8765")
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
