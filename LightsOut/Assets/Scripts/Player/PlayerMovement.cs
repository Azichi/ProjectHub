using UnityEngine;

using UnityEngine.Rendering.Universal;

public class PlayerMovement : MonoBehaviour
{
    public float moveSpeed = 5f;
    public float jumpForce = 7f;
    public Rigidbody2D rb;
    public Transform groundCheck;
    public LayerMask groundLayer;
    public PlayerShooting playerShooting;
    public Animator animator;

    public Transform firePoint;  
    public Light2D flashlight;  

    private bool isGrounded;
    private float groundCheckRadius = 0.1f;
    private bool facingRight = true; 

    public bool isAiming = false;
    public bool isDead = false;

    private AudioSource audioSource;
    public AudioClip[] walkSounds;
    public AudioClip jumpSound;
    public AudioClip landingSound;

    public float walkSoundCooldown = 0.35f;
    private float nextWalkSoundTime = 0f; 

    void Start()
    {
        if (firePoint != null && flashlight == null)
        {
            flashlight = firePoint.GetComponentInChildren<Light2D>();
        }

        audioSource = gameObject.AddComponent<AudioSource>();
        audioSource.playOnAwake = false;
    }

    void Update()
    {
        isGrounded = Physics2D.OverlapCircle(groundCheck.position, groundCheckRadius, groundLayer);
        animator.SetBool("IsGrounded", isGrounded);

        float moveInput = Input.GetAxisRaw("Horizontal");
        rb.linearVelocity = new Vector2(moveInput * moveSpeed, rb.linearVelocity.y);

        if (Mathf.Abs(moveInput) > 0.1f && isGrounded && Time.time >= nextWalkSoundTime)
        {
            PlayWalkSound();
            nextWalkSoundTime = Time.time + walkSoundCooldown;
        }
        if (Input.GetButtonDown("Jump") && isGrounded)
        {
            Jump();
        }

        animator.SetFloat("Speed", Mathf.Abs(moveInput));
        animator.SetBool("IsWalking", Mathf.Abs(moveInput) > 0 && isGrounded);

        HandleAimingAndFlipping();
    }

    void Jump()
    {
        rb.linearVelocity = new Vector2(rb.linearVelocity.x, jumpForce);
        animator.Play("Jump");

        if (jumpSound != null)
        {
            audioSource.PlayOneShot(jumpSound);
        }
    }

    void PlayWalkSound()
    {
        if (walkSounds.Length > 0)
        {
            AudioClip clip = walkSounds[Random.Range(0, walkSounds.Length)];
            audioSource.PlayOneShot(clip);
        }
    }

    void OnCollisionEnter2D(Collision2D collision)
    {
        if (collision.gameObject.CompareTag("Ground"))
        {
            isGrounded = true;

            if (landingSound != null)
            {
                audioSource.PlayOneShot(landingSound);
            }
        }
    }

    void HandleAimingAndFlipping()
    {
        Vector3 mousePosition = Camera.main.ScreenToWorldPoint(Input.mousePosition);
        Vector2 direction = mousePosition - transform.position;

        if (direction.x > 0 && !facingRight)
        {
            Flip();
        }
        else if (direction.x < 0 && facingRight)
        {
            Flip();
        }
    }

    void Flip()
    {
        facingRight = !facingRight;

        Vector3 scale = transform.localScale;
        scale.x *= -1;
        transform.localScale = scale;

        if (firePoint != null)
        {
            Vector3 firePointScale = firePoint.localScale;
            firePointScale.x *= -1;
            firePoint.localScale = firePointScale;

            if (flashlight != null)
            {
                flashlight.transform.localScale = firePoint.localScale;
            }
        }

        playerShooting.SetFacingDirection(facingRight);
    }
}
