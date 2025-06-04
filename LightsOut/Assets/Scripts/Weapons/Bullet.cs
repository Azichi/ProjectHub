using UnityEngine;

public class Bullet : MonoBehaviour
{
    public float bulletLifetime = 3f;
    public int bulletDamage = 10;

    void Start()
    {
        Destroy(gameObject, bulletLifetime);
    }

    void OnCollisionEnter2D(Collision2D collision)
    {
        PlayerHealth player = collision.gameObject.GetComponent<PlayerHealth>();
        ZombieHealth zombie = collision.gameObject.GetComponent<ZombieHealth>();

        if (player != null)
        {
            player.TakeDamage(bulletDamage);
        }
        else if (zombie != null)
        {
            zombie.TakeDamage(bulletDamage);
        }

        Destroy(gameObject);
    }
}
