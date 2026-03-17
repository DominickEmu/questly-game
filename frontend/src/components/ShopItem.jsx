import styles from './ShopItem.module.css';

const EQUIPPABLE = new Set(['hat', 'face', 'body', 'hand']);

export default function ShopItem({ item, onBuy, isOwned, isEquipped, onEquip, onUnequip }) {
  const canEquip = EQUIPPABLE.has(item.category);

  return (
    <div className={`${styles.card} ${isEquipped ? styles.equippedCard : ''}`}>
      {item.image_url && (
        <div className={styles.imageWrap}>
          <img src={item.image_url} alt={item.name} className={styles.image} />
        </div>
      )}
      <div className={styles.badge}>{item.category}</div>
      <h3 className={styles.name}>{item.name}</h3>
      <p className={styles.desc}>{item.description}</p>

      <div className={styles.footer}>
        {isEquipped ? (
          <div className={styles.equippedRow}>
            <span className={styles.equippedBadge}>✓ Equipped</span>
            <button className={styles.unequipBtn} onClick={() => onUnequip(item.category)}>
              Remove
            </button>
          </div>
        ) : isOwned && canEquip ? (
          <button className="btn-primary" onClick={() => onEquip(item.id)}>
            Equip
          </button>
        ) : (
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
        )}
      </div>
    </div>
  );
}
