import { useState, useEffect } from 'react';
import ShopItem from '../components/ShopItem';
import { api } from '../api';
import styles from './Shop.module.css';

const EQUIPPABLE_CATEGORIES = ['hat', 'face', 'body', 'hand'];
const CATEGORY_LABELS = { hat: 'Hats', face: 'Face', body: 'Body', hand: 'Hand' };

export default function Shop({ profile, onPurchase }) {
  const [items, setItems] = useState([]);
  const [purchases, setPurchases] = useState([]);
  const [message, setMessage] = useState(null);
  const [isError, setIsError] = useState(false);

  const refreshData = () => {
    api.getShopItems().then(setItems);
    api.getPurchases().then(setPurchases);
    onPurchase(); // refresh profile (balance + equipped state)
  };

  useEffect(() => {
    api.getShopItems().then(setItems);
    api.getPurchases().then(setPurchases);
  }, []);

  const showMsg = (msg, err = false) => {
    setMessage(msg);
    setIsError(err);
    setTimeout(() => setMessage(null), 2500);
  };

  const handleBuy = async (itemId, currency) => {
    try {
      await api.buyItem(itemId, currency);
      showMsg('Item purchased!');
      refreshData();
    } catch (err) {
      showMsg(err.message, true);
    }
  };

  const handleEquip = async (itemId) => {
    try {
      await api.equipItem(itemId);
      showMsg('Item equipped!');
      onPurchase();
    } catch (err) {
      showMsg(err.message, true);
    }
  };

  const handleUnequip = async (slot) => {
    try {
      await api.unequipSlot(slot);
      showMsg('Item removed.');
      onPurchase();
    } catch (err) {
      showMsg(err.message, true);
    }
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

      <h2 className={styles.sectionHeader}>Accessories</h2>
      {EQUIPPABLE_CATEGORIES.map((cat) =>
        byCategory[cat].length > 0 ? (
          <div key={cat} className={styles.categoryBlock}>
            <h3 className={styles.categoryLabel}>{CATEGORY_LABELS[cat]}</h3>
            <div className={styles.grid}>
              {byCategory[cat].map((item) => (
                <ShopItem
                  key={item.id}
                  item={item}
                  onBuy={handleBuy}
                  isOwned={ownedIds.has(item.id)}
                  isEquipped={equippedIds.has(item.id)}
                  onEquip={handleEquip}
                  onUnequip={handleUnequip}
                />
              ))}
            </div>
          </div>
        ) : null
      )}

      {rewardItems.length > 0 && (
        <>
          <h2 className={styles.sectionHeader}>Rewards</h2>
          <div className={styles.grid}>
            {rewardItems.map((item) => (
              <ShopItem
                key={item.id}
                item={item}
                onBuy={handleBuy}
                isOwned={ownedIds.has(item.id)}
                isEquipped={false}
                onEquip={() => {}}
                onUnequip={() => {}}
              />
            ))}
          </div>
        </>
      )}

      {purchases.length > 0 && (
        <>
          <h2 className={styles.section}>Purchase History</h2>
          <ul className={styles.purchaseList}>
            {purchases.map((p) => (
              <li key={p.id}>
                {p.item.name} —{' '}
                <span className={styles.date}>
                  {new Date(p.purchased_at).toLocaleDateString()}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
