import { Activity, FileCheck, Users } from 'lucide-react';
import InsightMetrics from '../components/ui/InsightMetrics';

// Импортируем ваши фотографии из папки src/images
import solikhaImg from '../images/solikha.jpg';
import sanjarImg from '../images/sanjar.jpg';
import asilbekImg from '../images/asilbek.png';

export default function TeamInfo() {
  const team = [
    { 
      name: 'Dagarova Solikha', 
      role: 'CV & ML Engineer', 
      image: solikhaImg, 
      desc: 'Data Science & ML problem solver. 2× EGOI Representative. Co-developed Part A (event detection) and Part B (accident anticipation): focused on model architecture, custom rules, and experiments.',
      links: [
        { name: 'LINKEDIN ↗', url: 'https://www.linkedin.com/in/solikha-dagarova-198b01267/' },
        { name: 'GITHUB ↗', url: 'https://github.com/likha7' },
        { name: 'LEETCODE ↗', url: 'https://leetcode.com/u/likha/' },
        { name: 'CODEFORCES ↗', url: 'https://codeforces.com/profile/likhaa' }
      ]
    },
    { 
      name: 'Torexanov Sanjar', 
      role: 'Software Engineer / Full Stack', 
      image: sanjarImg, 
      desc: 'Software Engineer at Ipoteka Bank (OTP Group). Developed the website architecture, live demo implementation, EDA dashboards, and real-time inference visualization.',
      links: [
        { name: 'LINKEDIN ↗', url: 'https://www.linkedin.com/in/sanjar-torexanov-448279325/' },
        { name: 'GITHUB ↗', url: 'https://github.com/' }
      ]
    },
    { 
      name: 'Yakshinboyev Asilbek', 
      role: 'Data Science & ML', 
      image: asilbekImg, 
      desc: 'Top-300 Yandex Uzbekistan. Experienced ML Engineer (Smart Chatbot, Rasa). Co-developed Part A and Part B: focused on dataset processing, model integration, and pipeline optimization.',
      links: [
        { name: 'LINKEDIN ↗', url: 'https://www.linkedin.com/in/yakshinboyev/' },
        { name: 'GITLAB ↗', url: 'https://gitlab.com/yakshinboyev' },
        { name: 'LEETCODE ↗', url: 'https://leetcode.com/u/yakshinboyev/' }
      ]
    }
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
      <div>
        <h2 style={{ margin: 0, color: '#fff', fontSize: '28px', textShadow: '0 0 20px rgba(255,71,87,0.4)' }}>
          MARS team
        </h2>
        <p style={{ color: '#8b949e', fontSize: '16px', maxWidth: '600px', marginTop: '12px', lineHeight: '1.6' }}>
          Official submission: <a href="https://github.com/likha7/mars-wiut-cv-2026/releases/tag/v1.0" style={{ color: '#ff4757', textDecoration: 'none' }}>Release v1.0</a>. 
          YOLO11s model weights are available in the repository.
        </p>
      </div>

      <InsightMetrics
        label="Team and submission summary"
        items={[
          { label: 'Team members', value: team.length, detail: 'Computer vision track', icon: Users, tone: 'cyan' },
          { label: 'Pipeline parts', value: '2', detail: 'Events + risk', icon: Activity, tone: 'mars' },
          { label: 'Submission', value: 'v1.0', detail: 'Official release', icon: FileCheck, tone: 'amber' },
        ]}
      />

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(min(100%, 300px), 1fr))', gap: '20px' }}>
          {team.map((member) => (
            <div key={member.name} style={{
            background: 'rgba(20, 22, 30, 0.4)', backdropFilter: 'blur(12px)',
            padding: '26px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)',
            boxShadow: '0 10px 30px rgba(0,0,0,0.2)', transition: 'all 0.3s ease',
            display: 'flex', flexDirection: 'column'
          }}
          onMouseOver={(e) => { e.currentTarget.style.border = '1px solid rgba(255, 71, 87, 0.5)'; e.currentTarget.style.transform = 'translateY(-5px)'; }}
          onMouseOut={(e) => { e.currentTarget.style.border = '1px solid rgba(255,255,255,0.08)'; e.currentTarget.style.transform = 'translateY(0)'; }}>
            
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '20px' }}>
              <img 
                src={member.image} 
                alt={member.name} 
                style={{ 
                  width: '64px', 
                  height: '64px', 
                  borderRadius: '12px', 
                  objectFit: 'cover', 
                  border: '2px solid rgba(255,71,87,0.3)' 
                }} 
              />
              <div>
                <h3 style={{ color: '#fff', fontSize: '20px', margin: '0 0 6px 0' }}>{member.name}</h3>
                <div style={{ color: '#ff4757', fontWeight: '600', fontSize: '13px', letterSpacing: '0.5px' }}>{member.role.toUpperCase()}</div>
              </div>
            </div>

            <p style={{ color: '#8b949e', lineHeight: '1.6', margin: '0 0 24px 0', fontSize: '14px', flexGrow: 1 }}>{member.desc}</p>
            
            <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
              {member.links.map((link) => (
                <a 
                  key={link.name}
                  href={link.url} 
                  target="_blank" 
                  rel="noopener noreferrer" 
                  style={{ color: '#8b949e', textDecoration: 'none', fontSize: '13px', fontWeight: '600', transition: 'color 0.2s' }} 
                  onMouseOver={(e) => e.currentTarget.style.color = '#fff'} 
                  onMouseOut={(e) => e.currentTarget.style.color = '#8b949e'}
                >
                  {link.name}
                </a>
              ))}
            </div>

          </div>
        ))}
      </div>
    </div>
  );
}