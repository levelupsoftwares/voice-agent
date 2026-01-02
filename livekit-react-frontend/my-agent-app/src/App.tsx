'use client';

import { useEffect, useState } from 'react';
import {
  LiveKitRoom,
  ControlBar,
  RoomAudioRenderer,
  BarVisualizer,
  useLocalParticipant,
} from '@livekit/components-react';
import '@livekit/components-styles';

const LIVEKIT_URL = 'wss://voice-agent-an5zldp0.livekit.cloud';

export default function App() {
  const [token, setToken] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchToken() {
      try {
        const res = await fetch('http://localhost:3001/token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            room: 'demo-room',
            identity: 'browser-user',
          }),
        });

        if (!res.ok) {
          const text = await res.text();
          throw new Error(text);
        }

        const data = await res.json();

        if (!data.token) {
          throw new Error('Token missing in response');
        }

        setToken(data.token);
      } catch (err: any) {
        console.error(err);
        setError(err.message || 'Failed to fetch token');
      }
    }

    fetchToken();
  }, []);

  if (error) {
    return (
      <div style={{ padding: '2rem', color: 'red' }}>
        <h2>Error</h2>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <LiveKitRoom
      token={token}
      serverUrl={LIVEKIT_URL}
      connect={Boolean(token)}
      audio
      video={false}
      data-lk-theme="default"
      style={{ height: '100vh' }}
    >
      <MicVisualizer />

      <ControlBar
        controls={{
          microphone: true,
          camera: false,
          screenShare: false,
        }}
      />

      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}

/**
 * Visualizes the LOCAL user's microphone audio
 * (agent audio is rendered automatically by RoomAudioRenderer)
 */
function MicVisualizer() {
  const { microphoneTrack } = useLocalParticipant();
  const audioTrack = microphoneTrack?.audioTrack;
   return (
    <div style={{ height: '300px', padding: '1rem' }}>
      <h3>Microphone Activity</h3>

      {audioTrack ? (
        <BarVisualizer
          track={audioTrack}
          barCount={5}
        />
      ) : (
        <p>Microphone not active</p>
      )}
    </div>
  );
}
