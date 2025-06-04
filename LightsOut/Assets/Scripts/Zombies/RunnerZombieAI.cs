using System.Collections;
using UnityEngine;

public class RunnerZombieAI : MonoBehaviour
{
    public Transform player;
    public float baseMoveSpeed = 3.5f; 
    public int damage = 15; 
    public float pushForce = 10f;

    private bool facingRight = true;
    private Animator animator;
    private Rigidbody2D rb;

    private AudioSource audioSource; 
    public AudioClip[] runSounds;   
    public AudioClip[] attackSounds;
    public float soundTriggerDistance = 5f; 
    private float runSoundCooldown = 0.125f; 
    private float nextRunSoundTime = 0f; 



    void Start()
    {
        rb = GetComponent<Rigidbody2D>();
        animator = GetComponent<Animator>();
        audioSource = gameObject.AddComponent<AudioSource>();
        audioSource.playOnAwake = false;

        baseMoveSpeed *= DifficultyManager.Instance.speedMultiplier;
        damage = Mathf.RoundToInt(damage * DifficultyManager.Instance.damageMultiplier);


        if (player == null)
        {
            player = GameObject.FindWithTag("Player")?.transform;
            if (player == null)
            {
                enabled = false;
                return;
            }
        }
    }

    void Update()
    {
        if (player != null)
        {
            Vector3 direction = (player.position - transform.position).normalized;
            rb.linearVelocity = new Vector2(direction.x * baseMoveSpeed, rb.linearVelocity.y);

            animator.SetBool("IsRunning", true);
            if (player != null && Vector2.Distance(transform.position, player.position) <= soundTriggerDistance)
            {
                if (Time.time >= nextRunSoundTime) 
                {
                    if (runSounds.Length > 0)
                    {
                        AudioClip clip = runSounds[Random.Range(0, runSounds.Length)];
                        audioSource.PlayOneShot(clip);

                        nextRunSoundTime = Time.time + runSoundCooldown;
                    }
                }
            }

            if (player.position.x < transform.position.x && facingRight)
                Flip();
            else if (player.position.x > transform.position.x && !facingRight)
                Flip();
        }
    }

    void Flip()
    {
        facingRight = !facingRight;
        Vector3 scale = transform.localScale;
        scale.x *= -1;
        transform.localScale = scale;
    }

    void OnCollisionEnter2D(Collision2D collision)
    {
        if (collision.gameObject.CompareTag("Player"))
        {
            PlayerHealth playerHealth = collision.gameObject.GetComponent<PlayerHealth>();
            if (playerHealth != null)
            {
                playerHealth.TakeDamage(damage);
                animator.SetBool("IsAttacking", true);
                if (attackSounds.Length > 0)
                {
                    AudioClip clip = attackSounds[Random.Range(0, attackSounds.Length)];
                    audioSource.PlayOneShot(clip);
                }

            }

            Rigidbody2D playerRb = collision.gameObject.GetComponent<Rigidbody2D>();
            if (playerRb != null)
            {
                Vector2 pushDirection = (collision.transform.position - transform.position).normalized;
                playerRb.linearVelocity = new Vector2(pushDirection.x * pushForce, playerRb.linearVelocity.y);
            }
        }
    }

    void OnCollisionStay2D(Collision2D collision)
    {
        if (collision.gameObject.CompareTag("Player"))
        {
            Rigidbody2D playerRb = collision.gameObject.GetComponent<Rigidbody2D>();
            if (playerRb != null)
            {
                Vector2 pushDirection = (collision.transform.position - transform.position).normalized;
                playerRb.linearVelocity = new Vector2(pushDirection.x * pushForce, playerRb.linearVelocity.y);
            }
        }
    }

    void OnCollisionExit2D(Collision2D collision)
    {
        if (collision.gameObject.CompareTag("Player"))
        {
            animator.SetBool("IsAttacking", false); // Reset attack animation when not colliding
        }
    }
}
