import { useState, useEffect, useCallback } from 'react';
import ShopItem from '../components/ShopItem';
import { api } from '../api';
import styles from './Shop.module.css';

const EQUIPPABLE_CATEGORIES = ['hat', 'face', 'body', 'hand'];
const CATEGORY_LABELS = { hat: 'Hats', face: 'Face', body: 'Body', hand: 'Hand' };
const TIMER_PRESETS = [
  { label: '15 min', minutes: 15 },
  { label: '30 min', minutes: 30 },
  { label: '1 hr',   minutes: 60 },
  { label: '2 hr',   minutes: 120 },
];

function loadTimers() {
  try { return JSON.parse(localStorage.getItem('questly_timers') || '{}'); }
  catch { return {}; }
}
function saveTimers(t) { localStorage.setItem('questly_timers', JSON.stringify(t)); }

function formatCountdown(ms) {
  if (ms <= 0) return '0:00';
  const s = Math.floor(ms / 1000);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = s % 60;
  if (h > 0) return `${h}:${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
  return `${m}:${String(sec).padStart(2, '0')}`;
}

export default function Shop({ profile, onPurchase }) {
  const [items, setItems] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [message, setMessage] = useState(null);
  const [isError, setIsError] = useState(false);
  const [timers, setTimers] = useState(loadTimers);
  const [pickerItemId, setPickerItemId] = useState(null);
  const [, setTick] = useState(0);

  const refreshData = () => {
    api.getShopItems().then(setItems);
    api.getPurchases().then(setPurchases);
    onPurchase();
  };

  useEffect(() => {
    api.getShopItems().then(setItems);
    api.getPurchases().then(setPurchases);
  }, []);

  // Tick every second while any timer is active
  useEffect(() => {
    const hasActive = Object.values(timers).some((t) => t && t.endTime > Date.now());
    if (!hasActive) return;
    const id = setInterval(() => setTick((n) => n + 1), 1000);
    return () => clearInterval(id);
  }, [timers]);

  const showMsg = (msg, err = false) => {
    setMessage(msg); setIsError(err);
    setTimeout(() => setMessage(null), 2500);
  };

  const handleBuy = async (itemId, currency) => {
    try { await api.buyItem(itemId, currency); showMsg('Item purchased!'); refreshData(); }
    catch (err) { showMsg(err.message, true); }
  };

  const handleBuyReward = async (item, currency) => {
    try { await api.buyItem(item.id, currency); refreshData(); setPickerItemId(item.id); }
    catch (err) { showMsg(err.message, true); }
  };

  const startTimer = useCallback((itemId, minutes) => {
    const next = { ...loadTimers(), [itemId]: { endTime: Date.now() + minutes * 60000, minutes } };
    saveTimers(next); setTimers(next); setPickerItemId(null);
  }, []);

  const clearTimer = useCallback((itemId) => {
    const next = { ...loadTimers(), [itemId]: null }; saveTimers(next); setTimers(next);
  }, []);

  const handleEquip = async (itemId) => {
    try { await api.equipItem(itemId); showMsg('Item equipped!'); onPurchase(); }
    catch (err) { showMsg(err.message, true); }
  };

  const handleUnequip = async (slot) => {
    try { await api.unequipSlot(slot); showMsg('Item removed.'); onPurchase(); }
    catch (err) { showMsg(err.message, true); }
  };

  const ownedIds = new Set(purchases.map((p) => p.shop_item_id));
  const equippedIds = new Set(
    EQUIPPABLE_CATEGORIES.map((slot) => profile?.[`equipped_${slot}`]).filter(Boolean)
  );
  const equippableItems = items.filter((i) => EQUIPPABLE_CATEGORIES.includes(i.category));
  const rewardItems = items.filter((i) => !EQUIPPABLE_CATEGORIES.includes(i.category));
  const byCategory = EQUIPPABLE_CATEGORIES.reduce((acc, cat) => {
    acc[cat] = equippableItems.filter((i) => i.category === cat);
    return acc;
  }, {});

  return (
    <div>
      <h1>Shop</h1>
      <p className={styles.balance}>
        🪙 {profile?.coins ?? 0} coins &nbsp;|&nbsp; 💎 {profile?.gems ?? 0} gems
      </p>
      {message && (
        <div className={`${styles.toast} ${isError ? styles.toastError : ''}`}>{message}</div>
      )}

      {/* ── Accessories ─────────────────────────────────── */}
      <h2 className={styles.sectionHeader}>Accessories</h2>
      {EQUIPPABLE_CATEGORIES.map((cat) =>
        byCategory[cat].length > 0 ? (
          <div key={cat} className={styles.categoryBlock}>
            <h3 className={styles.categoryLabel}>{CATEGORY_LABELS[cat]}</h3>
            <div className={styles.grid}>
              {byCategory[cat].map((item) => (
                <ShopItem key={item.id} item={item} onBuy={handleBuy}
                  isOwned={ownedIds.has(item.id)} isEquipped={equippedIds.has(item.id)}
                  onEquip={handleEquip} onUnequip={handleUnequip} />
              ))}
            </div>
          </div>
        ) : null
      )}

      {/* ── Rewards ─────────────────────────────────────── */}
      {rewardItems.length > 0 && (
        <>
          <h2 className={styles.sectionHeader}>Rewards</h2>
          <div className={styles.rewardGrid}>
            {rewardItems.map((item) => {
              const timer = timers[item.id];
              const isActive = timer && timer.endTime > Date.now();
              const isExpired = timer && timer.endTime <= Date.now();
              const remaining = isActive ? timer.endTime - Date.now() : 0;
              const showingPicker = pickerItemId === item.id;
              return (
                <div key={item.id} className={`${styles.rewardCard} ${isActive ? styles.rewardCardActive : ''}`}>
                  <div className={styles.rewardName}>{item.name}</div>
                  <div className={styles.rewardDesc}>{item.description}</div>

                  {isActive && (
                    <div className={styles.timerDisplay}>
                      <span className={styles.timerIcon}>⏱</span>
                      <span className={styles.timerCount}>{formatCountdown(remaining)}</span>
                      <span className={styles.timerLabel}>remaining</span>
                      <button className={styles.timerClear} onClick={() => clearTimer(item.id)} title="Clear timer">✕</button>
                    </div>
                  )}
                  {isExpired && !showingPicker && (
                    <div className={styles.timerExpired}>⌛ Time is up!</div>
                  )}
                  {showingPicker && (
                    <div className={styles.timerPicker}>
                      <p className={styles.timerPickerLabel}>How long is this reward?</p>
                      <div className={styles.timerPresets}>
                        {TIMER_PRESETS.map((p) => (
                          <button key={p.minutes} className={styles.timerPresetBtn}
                            onClick={() => startTimer(item.id, p.minutes)}>{p.label}</button>
                        ))}
                      </div>
                      <button className={styles.timerSkip} onClick={() => setPickerItemId(null)}>
                        Skip timer
                      </button>
                    </div>
                  )}
                  {!showingPicker && (
                    <div className={styles.rewardBuyRow}>
                      {item.price_coins > 0 && (
                        <button className={styles.rewardBuyBtn} onClick={() => handleBuyReward(item, 'coins')}>
                          🪙 {item.price_coins}
                        </button>
                      )}
                      {item.price_gems > 0 && (
                        <button className={styles.rewardBuyBtn} onClick={() => handleBuyReward(item, 'gems')}>
                          💎 {item.price_gems}
                        </button>
                      )}
                      {(isActive || isExpired) && (
                        <button className={styles.timerResetBtn} onClick={() => setPickerItemId(item.id)}>
                          ↺ Reset Timer
                        </button>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}

      {/* ── Purchase History ─────────────────────────────── */}
      {purchases.length > 0 && (
        <>
          <h2 className={styles.section}>Purchase History</h2>
          <ul className={styles.purchaseList}>
            {purchases.map((p) => (
              <li key={p.id}>
                {p.item.name} —{' '}
                <span className={styles.date}>{new Date(p.purchased_at).toLocaleDateString()}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
