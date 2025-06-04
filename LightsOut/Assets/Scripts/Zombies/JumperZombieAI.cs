using System.Collections;
using UnityEngine;

public class JumperZombieAI : MonoBehaviour
{
    public Transform player;
    public float baseMoveSpeed = 1f;
    public float jumpForce = 15f;
    public float attackRange = 1.5f;
    public float attackCooldown = 2f;
    public int damage = 20;
    public LayerMask groundLayer;
    public float jumpTowardsPlayerForce = 42f;

    private Animator animator;
    private Rigidbody2D rb;
    private bool isGrounded;
    private float lastAttackTime = 0f;
    private float lastJumpTime = 0f;
    private float nextJumpInterval;
    public Transform groundCheck;
    private enum ZombieAction { Idle, Attacking, Jumping }
    private ZombieAction currentAction = ZombieAction.Idle;
    public float jumpTowardsPlayerCooldown = 2f; 
    private float lastJumpAttemptTime = 0f; 

    private AudioSource audioSource; 
    public AudioClip[] runSounds;   
    public AudioClip[] jumpstartSounds;   
    public AudioClip[] jumplandSounds;   
    public AudioClip[] attackSounds; 
    public float soundTriggerDistance = 5f; 
    private float runSoundCooldown = 0.35f;
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

        if (groundCheck == null)
        {
            groundCheck = transform.Find("GroundCheck") ?? new GameObject("GroundCheck").transform;
            groundCheck.SetParent(transform);
            groundCheck.localPosition = new Vector3(0, -0.5f, 0);
        }

        if (animator == null)
        {
            enabled = false;
            return;
        }
    }

    void Update()
    {
        if (player == null) return;

        CheckGrounded();
        float distanceToPlayer = Vector2.Distance(transform.position, player.position);

        if (currentAction == ZombieAction.Idle)
        {
            if (distanceToPlayer <= attackRange && Time.time >= lastAttackTime + attackCooldown && isGrounded)
            {
                StartCoroutine(PerformAttack());
            }
            else if (isGrounded && Time.time >= lastJumpAttemptTime + jumpTowardsPlayerCooldown && distanceToPlayer > attackRange)
            {
                JumpTowardsPlayer();
                lastJumpAttemptTime = Time.time;
            }
            else if (isGrounded && distanceToPlayer > attackRange)
            {
              StalkTowardsPlayer();
            }
        }

        FlipTowardsPlayer();
    }



    void StalkTowardsPlayer()
    {
        if (isGrounded && currentAction == ZombieAction.Idle)
        {
            float distanceToPlayer = Vector2.Distance(transform.position, player.position);

            if (distanceToPlayer > attackRange)
            {
                Vector2 direction = (player.position - transform.position).normalized;
                rb.linearVelocity = new Vector2(direction.x * baseMoveSpeed, rb.linearVelocity.y);
                animator.SetBool("IsWalking", true);
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
            else
            {
                rb.linearVelocity = Vector2.zero;
                animator.SetBool("IsWalking", false);
            }
        }
    }

    void JumpTowardsPlayer()
    {
        if (currentAction != ZombieAction.Idle) return;

        currentAction = ZombieAction.Jumping;
        rb.linearVelocity = Vector2.zero;
        lastJumpTime = Time.time;

        Vector2 playerPosition = (Vector2)player.position;
        Rigidbody2D playerRb = player.GetComponent<Rigidbody2D>();
        Vector2 targetPosition = playerPosition;
        float distanceToPlayer = Vector2.Distance(transform.position, playerPosition);

        if (playerRb != null && playerRb.linearVelocity.magnitude > 0.1f)
        {
            float predictionTime = Mathf.Clamp(0.8f + (distanceToPlayer / 10f), 0.8f, 1.5f); 
            float forwardOffsetMultiplier = Mathf.Clamp(distanceToPlayer / 5f, 3f, 10f);

            Vector2 forwardOffset = playerRb.linearVelocity.normalized * forwardOffsetMultiplier;
            targetPosition = playerPosition + playerRb.linearVelocity * predictionTime + forwardOffset;
        }
        else
        {
            targetPosition = playerPosition + (playerPosition - (Vector2)transform.position).normalized * (attackRange - 0.1f);
        }

        Vector2 directionToTarget = (targetPosition - (Vector2)transform.position).normalized;
        float horizontalMultiplier = Mathf.Clamp(1.5f + (distanceToPlayer / 15f), 1.5f, 2.5f);
        Vector2 jumpDirection = new Vector2(directionToTarget.x * horizontalMultiplier, 1f) * jumpTowardsPlayerForce;

        rb.AddForce(jumpDirection, ForceMode2D.Impulse);


        animator.SetBool("IsJumping", true);
        animator.SetBool("IsWalking", false);
        isGrounded = false;
        PlayRandomSound(jumpstartSounds);

    }


    IEnumerator PerformAttack()
    {
        if (currentAction != ZombieAction.Idle || !isGrounded) yield break;

        currentAction = ZombieAction.Attacking;
        lastAttackTime = Time.time;

        rb.linearVelocity = Vector2.zero;
        animator.SetBool("IsWalking", false);
        animator.SetBool("IsAttacking", true);
        if (attackSounds.Length > 0)
        {
            AudioClip clip = attackSounds[Random.Range(0, attackSounds.Length)];
            audioSource.PlayOneShot(clip);
        }
        yield return new WaitForSeconds(0.4f);

        if (Vector2.Distance(transform.position, player.position) <= attackRange)
        {
            PlayerHealth playerHealth = player.GetComponent<PlayerHealth>();
            playerHealth?.TakeDamage(damage);
        }

        yield return new WaitForSeconds(0.4f);



        currentAction = ZombieAction.Jumping;
        animator.SetBool("IsAttacking", false);
        animator.SetBool("IsJumping", true);
 

        rb.linearVelocity = Vector2.zero; 
        float directionMultiplier = transform.localScale.x > 0 ? -1f : 1f;
        Vector2 jumpD = new Vector2(directionMultiplier, 1f) * jumpForce * 0.55f;
        rb.linearVelocity = Vector2.zero;
        rb.AddForce(jumpD, ForceMode2D.Impulse);

        yield return new WaitUntil(() => isGrounded);
        animator.SetBool("IsJumping", false);

        currentAction = ZombieAction.Idle;
    }


    void CheckGrounded()
    {
        isGrounded = Physics2D.OverlapCircle(groundCheck.position, 0.1f, groundLayer);

        if (isGrounded && currentAction == ZombieAction.Jumping)
        {
            animator.SetBool("IsJumping", false);
            currentAction = ZombieAction.Idle;
            PlayRandomSound(jumplandSounds);
        }
    }

    void PlayRandomSound(AudioClip[] soundArray)
    {
        if (soundArray.Length > 0)
        {
            AudioClip clip = soundArray[Random.Range(0, soundArray.Length)];
            audioSource.PlayOneShot(clip);
        }
    }

    void FlipTowardsPlayer()
    {
        if (isGrounded)
        {
            Vector3 scale = transform.localScale;
            scale.x = (player.position.x > transform.position.x) ? Mathf.Abs(scale.x) : -Mathf.Abs(scale.x);
            transform.localScale = scale;
        }
    }
}
