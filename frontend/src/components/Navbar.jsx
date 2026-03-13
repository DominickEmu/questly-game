import { NavLink } from 'react-router-dom';
import styles from './Navbar.module.css';

export default function Navbar({ profile }) {
  return (
    <nav className={styles.nav}>
      <div className={styles.brand}>Questly</div>
      <div className={styles.links}>
        <NavLink to="/" className={({ isActive }) => isActive ? styles.active : ''}>Dashboard</NavLink>
        <NavLink to="/weekly" className={({ isActive }) => isActive ? styles.active : ''}>Weekly</NavLink>
        <NavLink to="/calendar" className={({ isActive }) => isActive ? styles.active : ''}>Calendar</NavLink>
        <NavLink to="/shop" className={({ isActive }) => isActive ? styles.active : ''}>Shop</NavLink>
        <NavLink to="/story" className={({ isActive }) => isActive ? styles.active : ''}>Story</NavLink>
        <NavLink to="/profile" className={({ isActive }) => isActive ? styles.active : ''}>Profile</NavLink>
      </div>
      <div className={styles.currencies}>
        <span className={styles.coin}>🪙 {profile?.coins ?? 0}</span>
        <span className={styles.gem}>💎 {profile?.gems ?? 0}</span>
        <span className={styles.xp}>⚡ Lv{profile?.level ?? 1}</span>
      </div>
    </nav>
  );
}
