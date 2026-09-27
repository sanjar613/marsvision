import { motion } from 'framer-motion';

export default function HotzoneOverlay() {
  return (
    <svg 
      style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', pointerEvents: 'none', zIndex: 5 }}
      preserveAspectRatio="none"
    >
      {/* Animated region-of-interest polygon */}
      <motion.polygon 
        initial={{ opacity: 0 }}
        animate={{ opacity: [0.3, 0.6, 0.3] }}
        transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
        // Corner order: bottom-left, top-left, top-right, bottom-right.
        points="5%,95% 35%,55% 65%,55% 95%,95%" 
        fill="url(#dangerGradient)" 
        stroke="#ff4757" 
        strokeWidth="2" 
        strokeDasharray="8,8"
      />
      
      {/* Region fill gradient */}
      <defs>
        <linearGradient id="dangerGradient" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(255, 71, 87, 0)" />
          <stop offset="100%" stopColor="rgba(255, 71, 87, 0.2)" />
        </linearGradient>
      </defs>

      {/* Video overlay labels */}
      <text x="7%" y="90%" fill="#ff4757" fontFamily="monospace" fontSize="14" fontWeight="bold" style={{ textShadow: '0 0 8px rgba(255,71,87,0.8)' }}>
        [!] DANGER ZONE ACTV
      </text>
      <text x="7%" y="94%" fill="#e2e8f0" fontFamily="monospace" fontSize="10" opacity="0.7">
        ROI_ID: PEDESTRIAN_CROSSING_01
      </text>
    </svg>
  );
}