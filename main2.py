import json
import random
import math

import websockets
import asyncio

# Vars
CONNECTIONS = set()
TEMP = {
    "1XPos": 0,
    "1YPos": 0,
    "2XPos": 0,
    "2YPos": 0,
    "PaddleHeight": 0,
    "BallXPos": 0,
    "BallYPos": 0,
    "BallRadius": 0,
    "CanvasWidth": 0,
    "CanvasHeight": 0
}
PLAYER = {
    "1XPos": 0,
    "1YPos": 0,
    "2XPos": 0,
    "2YPos": 0,
    "PaddleHeight": 0,
    "BallXPos": 0,
    "BallYPos": 0,
    "BallRadius": 0,
    "CanvasWidth": 0,
    "CanvasHeight": 0
}
LASTPLAYER = 0
LOST = False
READY = [False, False]
VX = 0
VY = 0


def broadcast(message: str):
    websockets.broadcast(CONNECTIONS, message)


def update_struct(to_update: dict, payload: dict, current_player: int):
    to_update["1XPos"] = payload["1XPos"] if current_player == 1 else payload["2XPos"]
    to_update["1YPos"] = payload["1YPos"] if current_player == 1 else payload["2YPos"]
    to_update["2XPos"] = payload["2XPos"] if current_player == 1 else payload["1XPos"]
    to_update["2YPos"] = payload["2YPos"] if current_player == 1 else payload["1YPos"]
    to_update["PaddleHeight"] = payload["PaddleHeight"]
    to_update["BallXPos"] = payload["BallXPos"]
    to_update["BallYPos"] = payload["BallYPos"]
    to_update["BallRadius"] = payload["BallRadius"]
    to_update["CanvasWidth"] = payload["CanvasWidth"]
    to_update["CanvasHeight"] = payload["CanvasHeight"]


async def handler(websocket: websockets.WebSocketServerProtocol):
    global PLAYER, LOST, READY, TEMP, VX, VY, LASTPLAYER
    pnum = 0

    async for message in websocket:
        payload = json.loads(message)

        # Spieler Laden
        if pnum == 0:
            pnum = payload["CurrentPlayer"]
            # Daten im Server aktualisieren
            update_struct(PLAYER, payload, pnum)

        # Protokolle abarbeiten
        match payload["Protocol"]:
            # Spieler Bereit
            case "PlayerReady":
                READY[pnum - 1] = True
                if all(READY):
                    LOST = False

                    # Berechnen Ball
                    rbool = random.randrange(0, 1) == 0
                    if rbool:
                        VX = random.randrange(5, 10) / 10
                    else:
                        VX = random.randrange(-10, -5) / 10
                    VY = math.sin(math.acos(VX))

                    cw = PLAYER["CanvasWidth"]
                    ch = PLAYER["CanvasHeight"]

                    xb = 0
                    yb = 0
                    bx = xb + (ch / 2)
                    by = yb + (cw / 2)

                    PLAYER["BallXPos"] = int(bx)
                    PLAYER["BallYPos"] = int(by)
                    LASTPLAYER = pnum

                    broadcast(json.dumps({"Protocol": "GameStart", **PLAYER}))
            # Spieldaten erhalten
            case "GameData":
                # Player
                p1x = PLAYER["1XPos"]
                p1y = PLAYER["1YPos"]
                p2x = PLAYER["2XPos"]
                p2y = PLAYER["2YPos"]
                # Paddle
                ph = PLAYER["PaddleHeight"]
                # Ball
                bx = PLAYER["BallXPos"]
                by = PLAYER["BallYPos"]
                br = PLAYER["BallRadius"]
                # Canvas
                cw = PLAYER["CanvasWidth"]
                ch = PLAYER["CanvasHeight"]
                # Drehschrauben
                vp1 = payload["1YPos"] - p1y * 15
                vp2 = payload["2YPos"] - p2y * 15
                vpmax = 100
                vb = 1

                x1 = p1x + (ch / 2) + 70
                x2 = p2x + (ch / 2)
                y1 = p1y - (cw / 2) - ph / 2
                y2 = p2y - (cw / 2) - ph / 2
                xb = bx + (ch / 2)
                yb = by - (cw / 2)

                if x1 >= xb - br >= x1 - vb and y1 + ph / 2 >= yb - br and yb + br >= y1 - ph / 2:
                    VX = VX - 2 * vp1 / vpmax * VX
                    VY = math.sin(math.acos(VX))
                    vb = vb * 0.0001

                if x2 <= xb + br <= x2 + vb and y2 + ph / 2 >= yb - br and yb + br >= y2 - ph / 2:
                    VX = VX - 2 * vp2 / vpmax * VX
                    VY = math.sin(math.acos(VX))
                    vb = vb * 0.0001

                if -cw / 2 >= xb - br and xb + br >= cw / 2:
                    PLAYER = TEMP
                    LOST = True
                    READY = [False, False]
                    LASTPLAYER = 0
                    broadcast(
                        json.dumps(
                            {"Protocol": "GameEnd", "CurrentPlayer": 1 if -cw / 2 <= xb else 2, **PLAYER}
                        )
                    )
                    continue

                if ch / 2 <= yb + br and yb - br <= -ch / 2:
                    VY = -VY
                xb = xb + VX * vb
                yb = yb + VY * vb
                xb = round(xb, 0)
                yb = round(yb, 0)
                bx = xb + (ch / 2)
                by = yb + (cw / 2)

                PLAYER["BallXPos"] = int(bx)
                PLAYER["BallYPos"] = int(by)
                PLAYER["1XPos"] = payload["1XPos"]
                PLAYER["1YPos"] = payload["1YPos"]

                broadcast(json.dumps({"Protocol": "GameData", **PLAYER}))
            # Spiel zurücksetzen
            case "Reset":
                PLAYER = TEMP
                LOST = False
                READY = [False, False]
                VX = 0
                VY = 0
                broadcast(json.dumps({"Protocol": "Reset", **PLAYER}))


async def acceptor(websocket: websockets.WebSocketServerProtocol):
    CONNECTIONS.add(websocket)
    try:
        await handler(websocket)
    finally:
        CONNECTIONS.remove(websocket)


async def main():
    # MSO: 10.37.132.27
    # Privat: 192.168.178.66
    async with websockets.serve(acceptor, "10.37.132.27", 5174):
        print("server started")
        await asyncio.Future()  # läuft ewig


if __name__ == "__main__":
    asyncio.run(main())
