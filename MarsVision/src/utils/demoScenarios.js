export const demoScenarios = [
  {
    id: 'crosswalk-intrusion',
    title: 'Crosswalk intrusion',
    location: 'North crossing · CAM 01',
    summary: 'A pedestrian enters the carriageway outside the marked crossing.',
    duration: 30,
    events: [
      { label: 'jaywalking', start: 6.4, end: 10.2, confidence: 0.94, bbox: { x: 43, y: 34, w: 12, h: 29 } },
      { label: 'stopped_vehicle', start: 18.1, end: 23.5, confidence: 0.88, bbox: { x: 66, y: 46, w: 21, h: 27 } },
    ],
    risk_curve: [[0, 0.08], [3, 0.11], [6, 0.66], [8, 0.91], [10, 0.73], [13, 0.18], [18, 0.12], [21, 0.48], [24, 0.26], [30, 0.09]],
  },
  {
    id: 'junction-queue',
    title: 'Junction queue buildup',
    location: 'West approach · CAM 02',
    summary: 'A vehicle remains stationary as the queue clears around it.',
    duration: 30,
    events: [
      { label: 'stopped_vehicle', start: 8.2, end: 17.6, confidence: 0.89, bbox: { x: 28, y: 41, w: 24, h: 25 } },
    ],
    risk_curve: [[0, 0.1], [5, 0.12], [8, 0.28], [11, 0.62], [14, 0.78], [18, 0.7], [21, 0.31], [25, 0.15], [30, 0.1]],
  },
  {
    id: 'turning-conflict',
    title: 'Turning conflict',
    location: 'Central junction · CAM 03',
    summary: 'A turning vehicle and crossing pedestrian create a short risk spike.',
    duration: 30,
    events: [
      { label: 'jaywalking', start: 12.1, end: 16.7, confidence: 0.91, bbox: { x: 52, y: 37, w: 11, h: 30 } },
      { label: 'accident_risk', start: 13.5, end: 16.2, confidence: 0.82, bbox: { x: 38, y: 48, w: 28, h: 24 } },
    ],
    risk_curve: [[0, 0.06], [6, 0.1], [10, 0.16], [12, 0.58], [14, 0.89], [16, 0.94], [18, 0.36], [23, 0.13], [30, 0.07]],
  },
];
