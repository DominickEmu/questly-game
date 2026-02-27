import styles from './ShopItem.module.css';

export default function ShopItem({ item, onBuy }) {
  return (
    <div className={styles.card}>
      <div className={styles.badge}>{item.category}</div>
      <h3 className={styles.name}>{item.name}</h3>
      <p className={styles.desc}>{item.description}</p>
      <div className={styles.prices}>
        {item.price_coins > 0 && (
          <button className="btn-primary" onClick={() => onBuy(item.id, 'coins')}>
            🪙 {item.price_coins}
          </button>
        )}
        {item.price_gems > 0 && (
          <button className="btn-secondary" onClick={() => onBuy(item.id, 'gems')}>
            💎 {item.price_gems}
          </button>
        )}
      </div>
    </div>
  );
}
