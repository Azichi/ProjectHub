using UnityEngine;

public class ZombieHealth : MonoBehaviour
{
    public float maxHealth = 50;
    private float currentHealth;

    public Color damageFlashColor = Color.red;
    public float flashDuration = 0.1f;
    private SpriteRenderer spriteRenderer;
    private Color originalColor;

    public AudioClip[] deathSounds;
    private AudioSource audioSource;

    void Start()
    {
        currentHealth = maxHealth;
        audioSource = gameObject.AddComponent<AudioSource>();
        audioSource.playOnAwake = false;
        maxHealth *= DifficultyManager.Instance.healthMultiplier;
        currentHealth = maxHealth;

        spriteRenderer = GetComponent<SpriteRenderer>();
        if (spriteRenderer != null)
        {
            originalColor = spriteRenderer.color;
        }
    }

    public void TakeDamage(int damage)
    {
        currentHealth -= damage;

        if (spriteRenderer != null)
        {
            StartCoroutine(DamageFlash());
        }

        if (currentHealth <= 0)
        {
            Die();
        }
    }

    private System.Collections.IEnumerator DamageFlash()
    {
        spriteRenderer.color = damageFlashColor;

        yield return new WaitForSeconds(flashDuration);

        spriteRenderer.color = originalColor;
    }

    private bool isDying = false;

    void Die()
    {
        if (isDying) return;
        isDying = true;

        GameManager spawnManager = FindObjectOfType<GameManager>();
        if (spawnManager != null)
        {
            spawnManager.ZombieDied();
        }

        if (deathSounds.Length > 0)
        {
            AudioClip clip = deathSounds[Random.Range(0, deathSounds.Length)];

            GameObject tempAudio = new GameObject("TempAudio");
            AudioSource tempAudioSource = tempAudio.AddComponent<AudioSource>();
            tempAudioSource.clip = clip;
            tempAudioSource.playOnAwake = false;
            tempAudioSource.Play();

            Destroy(tempAudio, clip.length);
        }

        Destroy(gameObject);
    }


}
