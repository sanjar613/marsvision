import { create } from 'zustand';

export const useAppStore = create((set) => ({
  modelSettings: {
    confidenceThreshold: 0.45,
    iouThreshold: 0.50,
    enableRiskAnticipation: true,
  },
  
  systemAlert: null,
  activeCameras: [{ id: 'cam_01', name: 'Main Street and Lenin Street intersection', status: 'active' }],
  
  // Terminal log state.
  systemLogs: [
    { time: new Date().toLocaleTimeString(), type: 'info', message: 'MarsVision system initialized.' }
  ],

  updateModelSettings: (newSettings) => 
    set((state) => ({ modelSettings: { ...state.modelSettings, ...newSettings } })),
    
  triggerAlert: (message) => {
    set({ systemAlert: message });
    setTimeout(() => set({ systemAlert: null }), 5000);
  },

  // Append a log entry and retain only the newest 50.
  addLog: (log) => set((state) => {
    const newLogs = [...state.systemLogs, { time: new Date().toLocaleTimeString(), ...log }];
    return { systemLogs: newLogs.slice(-50) };
  })
}));