import './style.css'

import { Room } from "livekit-client";

async function connectToLiveKit() {
  // Step 4.1: fetch token from YOUR server
  const res = await fetch(
    "http://localhost:3001/token?room=demo-room&identity=browser-user"
  );
  const data  = await res.json();
  const token = data.token;

  // Safety check
  if (!token) {
    throw new Error("Token not received from server");
  }
  // Step 4.2: create room
  const room = new Room({
  rtcConfig: {
    iceTransportPolicy: "relay", //  FORCE TURN
  },
});

  // Step 4.3: connect using token
  await room.connect("wss://voice-agent-an5zldp0.livekit.cloud", token);

  console.log("Connected to room:", room.name);

  return room;
}

document.querySelector("#startButton").addEventListener("click", async () => {
  const room = await connectToLiveKit();
  console.log("Connected via button click:", room.name);
});
