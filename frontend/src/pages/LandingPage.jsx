import React, { useState } from 'react';
import { IntroAnimation } from '../components/landing/IntroAnimation';
import { LandingNavbar } from '../components/landing/LandingNavbar';
import { LandingHero } from '../components/landing/LandingHero';

export const LandingPage = ({ onEnterApp }) => {
  const [introDone, setIntroDone] = useState(false);

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: '#0a0f1d',
        overflowX: 'hidden',
        position: 'relative',
      }}
    >
      {/* Existing First Intro Animation (KEEP EXACTLY UNCHANGED) */}
      {!introDone && <IntroAnimation onComplete={() => setIntroDone(true)} />}

      {/* Compact Navbar */}
      <LandingNavbar onEnterApp={onEnterApp} />

      {/* Main Single-Viewport Gateway */}
      <main
        className="container"
        style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          paddingTop: '1rem',
          paddingBottom: '1.5rem',
        }}
      >
        <LandingHero onEnterApp={onEnterApp} />
      </main>
    </div>
  );
};

export default LandingPage;
