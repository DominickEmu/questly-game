import { useState, useEffect, useCallback } from 'react';
import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import Weekly from './pages/Weekly';
import Calendar from './pages/Calendar';
import Shop from './pages/Shop';
import Profile from './pages/Profile';
import Story from './pages/Story';
import Onboarding from './pages/Onboarding';
import { api } from './api';

export default function App() {
  const [profile, setProfile] = useState(null);

  const refreshProfile = useCallback(() => {
    api.getProfile().then(setProfile).catch(console.error);
  }, []);

  useEffect(() => { refreshProfile(); }, [refreshProfile]);

  // Apply genre theme to <html> so CSS [data-theme] selectors activate
  useEffect(() => {
    const genre = profile?.genre_preference || 'fantasy';
    if (genre === 'fantasy') {
      document.documentElement.removeAttribute('data-theme');
    } else {
      document.documentElement.setAttribute('data-theme', genre);
    }
  }, [profile?.genre_preference]);

  if (!profile) return null;

  if (!profile.setup_complete) {
    return <Onboarding profile={profile} onUpdate={refreshProfile} />;
  }

  return (
    <div className="app">
      <Navbar profile={profile} />
      <main className="main">
        <Routes>
          <Route path="/" element={<Dashboard profile={profile} onReward={refreshProfile} />} />
          <Route path="/weekly" element={<Weekly profile={profile} onReward={refreshProfile} />} />
          <Route path="/calendar" element={<Calendar profile={profile} onReward={refreshProfile} />} />
          <Route path="/shop" element={<Shop profile={profile} onPurchase={refreshProfile} />} />
          <Route path="/profile" element={<Profile profile={profile} onUpdate={refreshProfile} />} />
          <Route path="/story" element={<Story />} />
        </Routes>
      </main>
    </div>
  );
}
