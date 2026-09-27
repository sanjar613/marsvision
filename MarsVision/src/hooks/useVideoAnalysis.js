import { useState } from 'react';
import { useAppStore } from '../store/useAppStore';
import { analyzeVideo } from '../api/rest';

export function useVideoAnalysis() {
  const [result, setResult] = useState({ events: [], risk_curve: [], detections: [], risk_threshold: 0.25 });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const { addLog, triggerAlert } = useAppStore();
  const clearError = () => setError(null);

  const processVideo = async (file) => {
    if (!file) return;

    setLoading(true);
    setError(null);
    addLog({ type: 'info', message: `Initializing file upload: ${file.name} (${(file.size / 1024 / 1024).toFixed(2)} MB)` });

    try {
      addLog({ type: 'warning', message: 'Inference started. Awaiting response from MarsVision Engine...' });
      const data = await analyzeVideo(file);
      
      setResult({
        events: Array.isArray(data.events) ? data.events : [],
        risk_curve: Array.isArray(data.risk_curve) ? data.risk_curve : [],
        detections: Array.isArray(data.detections) ? data.detections : [],
        risk_threshold: Number.isFinite(data.risk_threshold) ? data.risk_threshold : 0.25
      });

      addLog({ type: 'success', message: `Analysis complete. Incidents detected: ${data.events?.length || 0}` });
      triggerAlert('Video analysis completed successfully!');

    } catch (err) {
      console.error(err);
      setError(err.message);
      addLog({ type: 'error', message: `Pipeline failure: ${err.message}` });
      triggerAlert('Error processing video. Please check the backend connection.');
    } finally {
      setLoading(false);
    }
  };

  return { result, loading, error, processVideo, clearError };
}