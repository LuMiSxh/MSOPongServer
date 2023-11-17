async def handler(websocket):
    while True:
        try:
            message = await websocket.recv()
        except websockets.ConnectionClosedOK:
            break
        try:
            payload = json.loads(message)
            # print(payload)
        except json.JSONDecodeError:
            break

        match payload["type"]:
            case "SD":

                if lost:
                    payload["type"] = "SE"
                    await websocket.send(json.dumps(payload))
                    continue

                # Paddles
                p1x = payload["P1X"]
                p1y = payload["P1Y"]
                p2x = payload["P2X"]
                p2y = payload["P2Y"]
                ph = payload["PH"]
                # Ball
                bx = payload["BX"]
                by = payload["BY"]
                br = payload["BR"]
                # Canvas
                cw = payload["CW"]
                ch = payload["CH"]
                # Drehschrauben
                vp1 = abs(game["P1Y"] - p1y) * 15
                vp2 = abs(game["P2Y"] - p2y) * 15
                vpmax = 100
                vb = 1

                vx = game["VX"]
                vy = game["VY"]
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
                    payload["P2X"] = game["P2X"]
                    payload["P2Y"] = game["P2Y"]
                    payload["CP"] = 1 if -cw / 2 <= xb else 2
                    lost = True
                    ready = [False, False]
                    payload["type"] = "SE"
                    game = temp1
                    await websocket.send(json.dumps(payload))
                    continue
                if ch / 2 <= yb <= -ch / 2:
                    vy = -vy
                xb = xb + vx * vb
                yb = yb + vy * vb
                bx = xb + (ch / 2)
                by = yb + (cw / 2)

                payload["BX"] = bx
                payload["BY"] = by
                payload["VX"] = vx
                payload["VY"] = vy
                if payload["CP"] != game["CP"]:
                    if payload["CP"] == 1:
                        payload["P2X"] = game["P2X"]
                        payload["P2Y"] = game["P2Y"]
                    else:
                        payload["P1X"] = game["P1X"]
                        payload["P1Y"] = game["P1Y"]
                game = payload
                await websocket.send(json.dumps(payload))

            case "SWB":
                if ready[0] and ready[1]:
                    payload["type"] = "SS"
                await websocket.send(json.dumps(payload))

            case "SB":
                cp = payload["CP"]
                print("Spieler bereit: ", cp)
                ready[cp - 1] = True
                print(ready)

                if ready[0] and ready[1]:
                    payload["type"] = "SS"
                    print("SIEG")
                await websocket.send(json.dumps(payload))

            case "SS":
                lost = False
                rbool = random.randrange(0, 1) == 0
                if rbool:
                    vx = random.randrange(5, 10) / 10
                else:
                    vx = random.randrange(-10, -5) / 10
                vy = random.randrange(-86, 86) / 100

                # Vektoren
                game["VX"] = vx
                game["VY"] = vy
                # Canvas
                cw = payload["CW"]
                ch = payload["CH"]

                xb = 0
                yb = 0
                bx = xb + (ch / 2)
                by = yb + (cw / 2)

                payload["BX"] = bx
                payload["BY"] = by
                game = payload
                await websocket.send(json.dumps(payload))

