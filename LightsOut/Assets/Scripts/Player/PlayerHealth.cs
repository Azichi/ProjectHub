using UnityEngine;
using System.Collections;


public class PlayerHealth : MonoBehaviour
{
    public int maxHealth = 100;
    public int currentHealth;
    public Animator animator;
    public SpriteRenderer spriteRenderer;
    public Color damageColor = Color.red;
    public float tintDuration = 0.1f;
    private GameManager gameManager;
    private AudioSource audioSource;
    public AudioClip[] damagesounds;
    public AudioClip deathsound;
    private CameraFollow cameraFollow; 

    void Start()
    {
        currentHealth = maxHealth;

        cameraFollow = Camera.main.GetComponent<CameraFollow>();
        audioSource = gameObject.AddComponent<AudioSource>();
        audioSource.playOnAwake = false;
    }

    public void TakeDamage(int damage)
    {
        currentHealth -= damage;
        StartCoroutine(DamageTint());
        if (damagesounds.Length > 0) 
        {
            AudioClip clip = damagesounds[Random.Range(0, damagesounds.Length)];
            audioSource.PlayOneShot(clip);
        }



        if (cameraFollow != null)
        {
            cameraFollow.TriggerShake();
        }

        if (currentHealth <= 0)
        {
            Die();
        }
    }

    private IEnumerator DamageTint()
    {
        spriteRenderer.color = damageColor;
        yield return new WaitForSeconds(tintDuration);
        spriteRenderer.color = Color.white;
    }

    public void Heal(int healAmount)
    {
        currentHealth += healAmount;
        if (currentHealth > maxHealth)
        {
            currentHealth = maxHealth;
        }
    }

    void Die()
    {
        if (animator != null)
            animator.SetBool("IsDead", true);


        CampaignManager campaignManager = FindObjectOfType<CampaignManager>();
        if (campaignManager != null)
        {
            campaignManager.PlayerDied();
        }
        else
        {
            GameManager gameManager = FindObjectOfType<GameManager>();
            if (gameManager != null)
            {
                gameManager.PlayerDied();
            }
            else
            {
            }
        }

        if (audioSource != null && deathsound != null)
        {
            audioSource.PlayOneShot(deathsound);
        }

    }


    void Respawn()
    {
        currentHealth = 100;
        animator.SetBool("IsDead", false);
        transform.position = new Vector3(0, 0, 0); 
    }

    public void RestoreHealth(int amount)
    {
        currentHealth = Mathf.Min(currentHealth + amount, maxHealth); 
    }
}
