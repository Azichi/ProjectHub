using System.Collections;
using UnityEngine;

public class BruteZombieAI : MonoBehaviour
{
    public Transform player;
    public float baseMoveSpeed = 2f;
    public float attackRange = 1.5f;
    public float attackCooldown = 2f;
    public int damage = 20;
    public float flipThreshold = 0.5f;


    private Animator animator;
    private Rigidbody2D rb;
    private bool isAttacking = false;
    private float lastAttackTime = 0f;

    private AudioSource audioSource;
    public AudioClip[] runSounds;  
    public AudioClip[] attackSounds; 
    public float soundTriggerDistance = 5f; 
    private float runSoundCooldown = 0.6f; 
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

        FlipTowardsPlayer();
    }

    void Update()
    {
        if (player == null) return;

        float distanceToPlayer = Vector2.Distance(transform.position, player.position);

        if (!isAttacking)
        {
            if (distanceToPlayer > attackRange)
            {
                MoveTowardsPlayer();
            }
            else
            {
                rb.linearVelocity = Vector2.zero;
                animator.SetBool("IsWalking", false);
                animator.SetBool("IsIdle", true);

                if (Time.time >= lastAttackTime + attackCooldown)
                {
                    StartCoroutine(PerformAttack());
                }
            }
        }

        FlipTowardsPlayer(); 
    }


    void MoveTowardsPlayer()
    {
        Vector2 direction = (player.position - transform.position).normalized;
        rb.linearVelocity = new Vector2(direction.x * baseMoveSpeed, rb.linearVelocity.y);

        animator.SetBool("IsWalking", true);
        animator.SetBool("IsAttacking", false);
        animator.SetBool("IsIdle", false);
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
    }

    void FlipTowardsPlayer()
    {
        if (player == null) return;

        float playerDirection = player.position.x - transform.position.x;
        bool shouldFlip = (playerDirection > flipThreshold && transform.localScale.x < 0) ||
                          (playerDirection < -flipThreshold && transform.localScale.x > 0);

        if (shouldFlip)
        {
            Vector3 scale = transform.localScale;
            scale.x *= -1;
            transform.localScale = scale;
        }
    }

    IEnumerator PerformAttack()
    {
        isAttacking = true;
        lastAttackTime = Time.time;

        rb.linearVelocity = Vector2.zero;
        animator.SetBool("IsWalking", false);
        animator.SetBool("IsIdle", false);
        animator.SetBool("IsAttacking", true);

        yield return new WaitForSeconds(0.5f);

        if (Vector2.Distance(transform.position, player.position) <= attackRange)
        {
            PlayerHealth playerHealth = player.GetComponent<PlayerHealth>();
            playerHealth?.TakeDamage(damage);
            if (attackSounds.Length > 0)
            {
                AudioClip clip = attackSounds[Random.Range(0, attackSounds.Length)];
                audioSource.PlayOneShot(clip);
            }
        }

        animator.SetBool("IsAttacking", false);
        animator.SetBool("IsWalking", false);
        animator.SetBool("IsIdle", true);
        isAttacking = false;
    }
}
