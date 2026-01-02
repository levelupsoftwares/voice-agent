import os
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from livekit import api
from dotenv import load_dotenv

load_dotenv(".env.local")

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

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

    token = (
        api.AccessToken(api_key, api_secret)
        .with_identity(identity)
        .with_name(identity)
        .with_grants(api.VideoGrants(room_join=True, room=room))
        .to_jwt()
    )

    # Force correct JSON content type
    response = make_response(jsonify({"token": token}))
    response.headers['Content-Type'] = 'application/json'
    return response

if __name__ == "__main__":
    print("🚀 Token server running on http://localhost:3001")
    app.run(host="0.0.0.0", port=3001, debug=True)
