import { useEffect } from 'react';
import { useAppStore } from '../store/useAppStore';
import { connectToAlerts } from '../api/websocket';

export function useLiveAlerts() {
  const { triggerAlert, addLog } = useAppStore();

  useEffect(() => {
    const ws = connectToAlerts();

    ws.onopen = () => {
      addLog({ type: 'success', message: 'WS_CONNECTION_ESTABLISHED: Listening to port 8000' });
    };

    ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      
      // Log the raw JSON payload for debugging.
      addLog({ type: 'cv_data', message: `PAYLOAD_RECEIVED: ${JSON.stringify(payload)}` });

      if (payload.type === 'CRITICAL_ALERT') {
        addLog({ type: 'error', message: `ACTION_REQUIRED: ${payload.data.message}` });
        triggerAlert(`[${payload.data.camera_id}] ${payload.data.message} (Risk: ${payload.data.risk_score * 100}%)`);
      }
    };

    ws.onerror = () => {
      addLog({ type: 'error', message: 'WS_CONNECTION_ERROR: Failed to connect to backend' });
    };

    ws.onclose = () => {
      addLog({ type: 'warning', message: 'WS_CONNECTION_CLOSED' });
    };

    return () => ws.close();
  }, [triggerAlert, addLog]);
}