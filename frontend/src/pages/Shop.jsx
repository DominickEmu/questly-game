import { useState, useEffect } from 'react';
import ShopItem from '../components/ShopItem';
import { api } from '../api';
import styles from './Shop.module.css';

export default function Shop({ profile, onPurchase }) {
  const [items, setItems] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [message, setMessage] = useState(null);

  useEffect(() => {
    api.getShopItems().then(setItems);
    api.getPurchases().then(setPurchases);
  }, []);

  const handleBuy = async (itemId, currency) => {
    try {
      await api.buyItem(itemId, currency);
      setMessage('Purchase successful!');
      onPurchase();
      api.getPurchases().then(setPurchases);
    } catch (err) {
      setMessage(err.message);
    }
    setTimeout(() => setMessage(null), 2500);
  };

  return (
    <div>
      <h1>Shop</h1>
      <p className={styles.balance}>
        Your balance: 🪙 {profile?.coins ?? 0} coins &nbsp;|&nbsp; 💎 {profile?.gems ?? 0} gems
      </p>

      {message && <div className={styles.toast}>{message}</div>}

      <div className={styles.grid}>
        {items.map((item) => (
          <ShopItem key={item.id} item={item} onBuy={handleBuy} />
        ))}
      </div>

      {purchases.length > 0 && (
        <>
          <h2 className={styles.section}>Your Purchases</h2>
          <ul className={styles.purchaseList}>
            {purchases.map((p) => (
              <li key={p.id}>
                {p.item.name} — <span className={styles.date}>{new Date(p.purchased_at).toLocaleDateString()}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
