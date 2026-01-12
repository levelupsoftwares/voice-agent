import os
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from livekit import api
from dotenv import load_dotenv
from livekit.api import LiveKitAPI, AccessToken, VideoGrants, RoomAgentDispatch
import asyncio


load_dotenv(".env.local")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
def get_livekit_api():
    return LiveKitAPI(
        api_url=os.getenv("LIVEKIT_URL"), 
        api_key=os.getenv("LIVEKIT_API_KEY"),
        api_secret=os.getenv("LIVEKIT_API_SECRET"),
    )

@app.route("/token", methods=["POST"])
def token():
    # Accept JSON body or query params
    data = request.get_json(silent=True)
    room = (data.get("room") if data else None) or request.args.get("room")
    identity = (data.get("identity") if data else None) or request.args.get("identity")

    if not room or not identity:
        return make_response(jsonify({"error": "room and identity required"}), 400)

    api_key = os.getenv("LIVEKIT_API_KEY")
    api_secret = os.getenv("LIVEKIT_API_SECRET")

    if not api_key or not api_secret:
        return make_response(jsonify({"error": "LiveKit credentials missing"}), 500)

    token_str = (
        api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(api.VideoGrants(room_join=True, room=room,room_create=True,can_publish=True))
        .to_jwt()
    )
    # print("token on the way",token_str)

    # Force correct JSON content type
    response = make_response(jsonify({"token": token_str}))
    # response.headers['Content-Type'] = 'application/json'
    return response

@app.route("/dispatch-agent", methods=["POST"])
def dispatch_agent():
    """Manually dispatch agent to room (required for LiveKit Cloud)"""
    data = request.get_json(silent=True) or {}
    room = data.get("room")
    
    if not room:
        return jsonify({"error": "room required"}), 400

    async def _dispatch():
        lk = get_livekit_api()
        try:
            # Dispatch the agent to the room
            await lk.agent.dispatch(
                agent_name="my-voice-agent",
                room=room,
            )
            print(f"✅ Agent dispatched to room: {room}")
        except Exception as e:
            print(f"❌ Failed to dispatch agent: {e}")
        finally:
            await lk.aclose()

    # Run the async dispatch
    asyncio.run(_dispatch())

    return jsonify({"ok": True, "room": room})

if __name__ == "__main__":
    print("🚀 Token server running on http://localhost:3001")
    app.run(host="0.0.0.0", port=3001, debug=True)
