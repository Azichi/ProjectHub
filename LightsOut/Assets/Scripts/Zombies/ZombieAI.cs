using UnityEngine;
using System.Collections;

public class ZombieAI : MonoBehaviour
{
    public Transform player;
    public float baseMoveSpeed = 1.5f;
    public float chargeMoveSpeed = 3f;
    public float closeRange = 3f;
    public float attackRange = 1.0f;
    public float attackDuration = 0.2f;
    public float attackScale = 1.2f;
    public float attackCooldown = 1.5f; 
    public Color attackColor = Color.red;
    public int damage = 15;
    public float pushForce = 10f;

    private bool facingRight = true;
    private Vector2 erraticOffset;
    private Vector3 originalScale;
    private Color originalColor;
    private bool isAttacking = false;
    private float nextAttackTime = 0f;

    private Animator animator;
    private SpriteRenderer spriteRenderer;
    private Rigidbody2D rb;

    private AudioSource audioSource;
    public AudioClip[] runSounds;
    public AudioClip[] attacksounds;
    public float soundTriggerDistance = 5f;
    private float runSoundCooldown = 0.45f; 
    private float nextRunSoundTime = 0f;  




    void Start()
    {
        originalScale = transform.localScale;
        spriteRenderer = GetComponent<SpriteRenderer>();
        animator = GetComponent<Animator>();
        rb = GetComponent<Rigidbody2D>();
        audioSource = gameObject.AddComponent<AudioSource>();
        audioSource.playOnAwake = false;

        baseMoveSpeed *= DifficultyManager.Instance.speedMultiplier;
        damage = Mathf.RoundToInt(damage * DifficultyManager.Instance.damageMultiplier);




        if (spriteRenderer != null)
        {
            originalColor = spriteRenderer.color;
        }

        if (player == null)
        {
            GameObject playerObj = GameObject.FindWithTag("Player");
            if (playerObj != null)
            {
                player = playerObj.transform;
            }
            else
            {
                enabled = false;
                return;
            }
        }
    }

    void Update()
    {
        if (player == null) return;

        float distanceToPlayer = Vector2.Distance(transform.position, player.position);

        if (!isAttacking && distanceToPlayer > attackRange)
        {
            MoveTowardsPlayer(distanceToPlayer);
        }

        if ((player.position.x < transform.position.x && facingRight) ||
            (player.position.x > transform.position.x && !facingRight))
        {
            Flip();
        }

        if (distanceToPlayer <= attackRange && Time.time >= nextAttackTime)
        {
            StartCoroutine(Attack());
        }

    }

    void MoveTowardsPlayer(float distanceToPlayer)
    {
        float currentMoveSpeed = distanceToPlayer <= closeRange ? chargeMoveSpeed : baseMoveSpeed;

        erraticOffset.x = Mathf.Sin(Time.time * 3) * 0.2f;

        Vector2 direction = new Vector2((player.position.x - transform.position.x) + erraticOffset.x, 0).normalized;
        rb.linearVelocity = new Vector2(direction.x * currentMoveSpeed, rb.linearVelocity.y);

        if (animator != null)
        {
            animator.SetBool("IsWalking", true);
        }
        if (!isAttacking && player != null && Vector2.Distance(transform.position, player.position) <= soundTriggerDistance)
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

    void StopMovement()
    {
        rb.linearVelocity = Vector2.zero;

        if (animator != null)
        {
            animator.SetBool("IsWalking", false);
        }
    }

    private IEnumerator Attack()
    {
        isAttacking = true;
        nextAttackTime = Time.time + attackCooldown;

        if (spriteRenderer != null) spriteRenderer.color = attackColor;

        Vector3 lungePosition = Vector3.MoveTowards(transform.position, player.position, attackRange * 0.5f);

        transform.position = lungePosition;

        if (animator != null) animator.SetTrigger("Attack");


        yield return new WaitForSeconds(attackDuration);

        if (spriteRenderer != null) spriteRenderer.color = originalColor;

        isAttacking = false;
    }


    void OnCollisionEnter2D(Collision2D collision)
    {
        if (collision.gameObject.CompareTag("Player") && Time.time >= nextAttackTime)
        {
            DealDamage(collision);
        }
    }

    void OnCollisionStay2D(Collision2D collision)
    {
        if (collision.gameObject.CompareTag("Player") && Time.time >= nextAttackTime)
        {
            DealDamage(collision);
        }
    }

    void OnCollisionExit2D(Collision2D collision)
    {
        if (collision.gameObject.CompareTag("Player"))
        {
            if (animator != null)
            {
                animator.SetBool("IsAttacking", false);
            }
        }
    }

    private void DealDamage(Collision2D collision)
    {
        PlayerHealth playerHealth = collision.gameObject.GetComponent<PlayerHealth>();
        if (playerHealth != null)
        {
            playerHealth.TakeDamage(damage);
            nextAttackTime = Time.time + attackCooldown;
            if (attacksounds.Length > 0)
            {
                audioSource.clip = attacksounds[Random.Range(0, attacksounds.Length)];
                audioSource.Play();
            }

            if (animator != null)
            {
                animator.SetBool("IsAttacking", true);
            }
        }

        Rigidbody2D playerRb = collision.gameObject.GetComponent<Rigidbody2D>();
        if (playerRb != null)
        {
            Vector2 pushDirection = (collision.transform.position - transform.position).normalized;
            playerRb.linearVelocity = new Vector2(pushDirection.x * pushForce, playerRb.linearVelocity.y);
        }
    }

    void Flip()
    {
        facingRight = !facingRight;
        Vector3 scale = transform.localScale;
        scale.x *= -1;
        transform.localScale = scale;
    }
}
