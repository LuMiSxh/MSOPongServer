import asyncio
import json
import random
import time
import websockets

# template
temp1 = {
    "CP": 1,
    "P1X": 0,
    "P1Y": 0,
    "P2X": 0,
    "P2Y": 0,
    "PH": 0,
    "BX": 0,
    "BY": 0,
    "BR": 0,
    "CW": 0,
    "CH": 0,
    "VX": 0,
    "VY": 0
}

GAME = {
    "CP": 1,
    "P1X": 0,
    "P1Y": 0,
    "P2X": 0,
    "P2Y": 0,
    "PH": 0,
    "BX": 0,
    "BY": 0,
    "BR": 0,
    "CW": 0,
    "CH": 0,
    "VX": 0,
    "VY": 0
}
LOST = False
READY = [False, False]



# Logic

CONNECTIONS = set()


def message_all(message: str):
    websockets.broadcast(CONNECTIONS, message)


async def register(websocket):
    CONNECTIONS.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        CONNECTIONS.remove(websocket)


async def game_handler():
    global GAME
    global LOST
    global READY
    global temp1
    while True:
        start_time = time.time()  # remember when we started
        p1 = None
        p2 = None

        message = {"type": "GMD"}
        message_all(json.dumps(message))

        if len(CONNECTIONS) != 2:
            await asyncio.sleep(1.0 - ((time.time() - start_time) % 1.0))
            continue

        for conn in CONNECTIONS:
            response = await conn.recv()
            temp = json.loads(response)
            if "current" not in temp:
                await asyncio.sleep(1.0 - ((time.time() - start_time) % 1.0))
                continue
            if temp["current"] == 1:
                p1 = temp
            elif temp["current"] == 2:
                p2 = temp

        if p1 is None or p2 is None:
            await asyncio.sleep(1.0 - ((time.time() - start_time) % 1.0))
            continue

        for player in [p1, p2]:
            match player["type"]:
                # SpielerBereit
                case "SB":
                    print("Request from: ", player["current"])
                    print(READY)
                    READY[player["current"] - 1] = True
                    if READY[0] and READY[1]:
                        message = {"type": "SS"}
                        message_all(json.dumps(message))

                # SpielStart
                case "SS":
                    LOST = False
                    # Berechnen Ball
                    rbool = random.randrange(0, 1) == 0
                    if rbool:
                        vx = random.randrange(5, 10) / 10
                    else:
                        vx = random.randrange(-10, -5) / 10
                    vy = random.randrange(-86, 86) / 100

                    # Vektoren
                    GAME["VX"] = vx
                    GAME["VY"] = vy
                    # Canvas
                    cw = player["CW"]
                    ch = player["CH"]

                    xb = 0
                    yb = 0
                    bx = xb + (ch / 2)
                    by = yb + (cw / 2)

                    player["BX"] = bx
                    player["BY"] = by
                    GAME = player

                    message_all(json.dumps(player))

                # SpielDaten
                case "SD":
                    # Paddles
                    p1x = player["P1X"]
                    p1y = player["P1Y"]
                    p2x = player["P2X"]
                    p2y = player["P2Y"]
                    ph = player["PH"]
                    # Ball
                    bx = player["BX"]
                    by = player["BY"]
                    br = player["BR"]
                    # Canvas
                    cw = player["CW"]
                    ch = player["CH"]
                    # Drehschrauben
                    vp1 = abs(GAME["P1Y"] - p1y) * 15
                    vp2 = abs(GAME["P2Y"] - p2y) * 15
                    vpmax = 100
                    vb = 1

                    vx = GAME["VX"]
                    vy = GAME["VY"]
                    x1 = p1x + (ch / 2)+70
                    x2 = p2x + (ch / 2)
                    y1 = p1y - (cw / 2)-ph/2
                    y2 = p2y - (cw / 2)-ph/2
                    xb = bx + (ch / 2)
                    yb = by - (cw / 2)
                    if x1 >= xb - br and y1 + ph / 2 >= yb >= y1 - ph / 2:
                        vx = vx - 2 * vp1 / vpmax * vx
                        vy = vy - 2 * vp1 / vpmax * vy
                        vb = vb * 0.001
                    if x2 >= xb + br and y2 + ph / 2 >= yb >= y2 - ph / 2:
                        vx = vx - 2 * vp2 / vpmax * vx
                        vy = vy - 2 * vp2 / vpmax * vy
                        vb = vb * 0.001
                    if -cw / 2 <= xb <= cw / 2:
                        player["P2X"] = GAME["P2X"]
                        player["P2Y"] = GAME["P2Y"]
                        player["current"] = 1 if -cw / 2 <= xb else 2
                        LOST = True
                        READY = [False, False]
                        player["type"] = "SE"
                        GAME = temp1
                        message_all(json.dumps(player))
                        continue
                    if ch / 2 <= yb <= -ch / 2:
                        vy = -vy
                    xb = xb + vx * vb
                    yb = yb + vy * vb
                    bx = xb + (ch / 2)
                    by = yb + (cw / 2)

                    player["BX"] = bx
                    player["BY"] = by
                    player["VX"] = vx
                    player["VY"] = vy
                    if player["CP"] != GAME["CP"]:
                        if player["CP"] == 1:
                            player["P2X"] = GAME["P2X"]
                            player["P2Y"] = GAME["P2Y"]
                        else:
                            player["P1X"] = GAME["P1X"]
                            player["P1Y"] = GAME["P1Y"]
                    GAME = player
                    message_all(json.dumps(player))
                case "GMD":
                    pass

        # If we finished fast, sleep the remaining time, to ensure we run 30 iterations per second
        await asyncio.sleep(1.0 - ((time.time() - start_time) % 1.0))


async def main():
    # MSO: 10.37.132.27
    # Privat: 192.168.178.66
    async with websockets.serve(register, "10.37.132.27", 5174):
        await game_handler()
        print("server started")
        await asyncio.Future()  # läuft ewig


if __name__ == "__main__":
    asyncio.run(main())
