using System.Collections;
using UnityEngine;

public class PlayerShooting : MonoBehaviour
{
    public GameObject bulletPrefab;
    public Transform firePoint;
    public float bulletSpeed = 20f;
    private bool isFacingRight = true;
    public Transform gunTransform;
    public GameObject gun;
    public ResourceManagement resourceManager;
    public float shakeIntensity = 0.05f;
    public float shakeSpeed = 10f;      

    private Vector3 gunOriginalPosition; 
    private bool isRunning;            
    private Animator animator; 

    public int meleeDamage = 25;
    public float meleeRange = 0.5f;
    public LayerMask Mobs;

    public GameObject knifePrefab;
    public Transform swordPoint;
    public float slashDuration = 0.2f;

    public float meleeCooldown = 1.0f; 
    private float nextMeleeTime = 0f; 
    private bool isReloading;

    private GameObject activeKnife;

    public AudioClip reloadSound;
    public AudioClip[] shootingSounds;
    private AudioSource audioSource;
    public AudioClip[] meleeSwingSounds; 
    public AudioClip[] meleeImpactSounds; 

    void Start()
    {
        resourceManager = GetComponent<ResourceManagement>();
        animator = GetComponent<Animator>();

        audioSource = GetComponent<AudioSource>();
        if (audioSource == null)
        {
            audioSource = gameObject.AddComponent<AudioSource>();
        }

        activeKnife = Instantiate(knifePrefab, swordPoint.position, Quaternion.identity, swordPoint);
        activeKnife.SetActive(false);
        if (gunTransform != null)
        {
            gunOriginalPosition = gunTransform.localPosition;
        }
    }

    void Update()
    {
            AnimatorStateInfo stateInfo = animator.GetCurrentAnimatorStateInfo(9);
            isRunning = stateInfo.IsName("IsRunning");

            if (isRunning && gunTransform != null)
            {
                float offsetX = Mathf.PerlinNoise(Time.time * shakeSpeed, 0) * 2 - 1;
                float offsetY = Mathf.PerlinNoise(0, Time.time * shakeSpeed) * 2 - 1;
                gunTransform.localPosition = gunOriginalPosition + new Vector3(offsetX, offsetY, 0) * shakeIntensity;
            }
            else if (gunTransform != null)
            {
                gunTransform.localPosition = gunOriginalPosition;
        }

        if (isReloading)
        {
            gunTransform.rotation = gunTransform.rotation;
            return;
        }

        if (Input.GetButtonDown("Fire1") && resourceManager.ammoCount > 0)
        {
            Shoot();
            resourceManager.ammoCount--;
        }

        if (Input.GetButtonDown("Fire2") && Time.time >= nextMeleeTime) 
        {
            MeleeAttack();
            nextMeleeTime = Time.time + meleeCooldown; 
        }

        if (Input.GetKeyDown(KeyCode.R) && !isReloading)
        {
            Reload(30);
        }

    }



    public void Reload(int ammoAmount)
    {
        if (isReloading) return; 

        StartCoroutine(ReloadRoutine(ammoAmount));
    }

    private IEnumerator ReloadRoutine(int ammoAmount)
    {
        isReloading = true;
        audioSource.PlayOneShot(reloadSound);

        Vector3 reloadOffset = new Vector3(-0.5f, -0.25f, 0);
        float reloadDuration = 1.5f;
        Vector3 initialPosition = gunTransform.localPosition;

        float elapsedTime = 0f;
        while (elapsedTime < reloadDuration / 2f)
        {
            elapsedTime += Time.deltaTime;
            gunTransform.localPosition = Vector3.Lerp(initialPosition, initialPosition + reloadOffset, elapsedTime / (reloadDuration / 2f));
            yield return null;
        }

        elapsedTime = 0f;
        while (elapsedTime < reloadDuration / 2f)
        {
            elapsedTime += Time.deltaTime;
            gunTransform.localPosition = Vector3.Lerp(initialPosition + reloadOffset, initialPosition, elapsedTime / (reloadDuration / 2f));
            yield return null;
        }

        gunTransform.localPosition = initialPosition;

        resourceManager.ammoCount += ammoAmount;
        if (resourceManager.ammoCount > 100)
        {
            resourceManager.ammoCount = 100;
        }

        isReloading = false;
    }



    void MeleeAttack()
    {
        if (audioSource != null && meleeSwingSounds.Length > 0)
        {
            AudioClip randomSwingSound = meleeSwingSounds[Random.Range(0, meleeSwingSounds.Length)];
            audioSource.PlayOneShot(randomSwingSound);
        }

        StartCoroutine(SlashEffect());

        Vector2 meleeCenter = isFacingRight ? (Vector2)transform.position + Vector2.right * meleeRange / 2
                                            : (Vector2)transform.position + Vector2.left * meleeRange / 2;

        Collider2D[] hitEnemies = Physics2D.OverlapCircleAll(meleeCenter, meleeRange, Mobs);

        foreach (Collider2D enemy in hitEnemies)
        {
            Vector2 directionToEnemy = enemy.transform.position - transform.position;
            bool isEnemyInFront = (isFacingRight && directionToEnemy.x > 0) || (!isFacingRight && directionToEnemy.x < 0);

            if (isEnemyInFront)
            {
                if (audioSource != null && meleeImpactSounds.Length > 0)
                {
                    AudioClip randomImpactSound = meleeImpactSounds[Random.Range(0, meleeImpactSounds.Length)];
                    audioSource.PlayOneShot(randomImpactSound);
                }


                enemy.GetComponent<ZombieHealth>()?.TakeDamage(meleeDamage);
            }
        }
    }

    private IEnumerator SlashEffect()
    {
        float elapsedTime = 0f;

        float startAngle = 0f;
        float endAngle = -135f;
        float totalRotation = endAngle - startAngle;

        activeKnife.SetActive(true);
        gun.SetActive(false);

        activeKnife.transform.localPosition = new Vector3(-0.25f, 3.5f, 0);
        activeKnife.transform.localRotation = Quaternion.Euler(0, 0, isFacingRight ? startAngle : -startAngle);

        while (elapsedTime < slashDuration)
        {
            elapsedTime += Time.deltaTime;
            float progress = elapsedTime / slashDuration;
            float currentAngle = Mathf.Lerp(startAngle, endAngle, progress) * (isFacingRight ? 1 : -1);
            activeKnife.transform.RotateAround(swordPoint.position, Vector3.forward, totalRotation * Time.deltaTime / slashDuration * (isFacingRight ? 1 : -1));

            yield return null;
        }

        activeKnife.transform.localRotation = Quaternion.identity;
        activeKnife.SetActive(false);
        gun.SetActive(true);
    }

    void Shoot()
    {
        GameObject bullet = Instantiate(bulletPrefab, firePoint.position, firePoint.rotation);
        Rigidbody2D rb = bullet.GetComponent<Rigidbody2D>();
        Vector2 shootingDirection = (firePoint.right).normalized;
        rb.linearVelocity = shootingDirection * bulletSpeed;

        if (shootingSounds.Length > 0)
        {
            int randomIndex = Random.Range(0, shootingSounds.Length); 
            AudioClip selectedClip = shootingSounds[randomIndex];

            if (selectedClip != null)
            {
                audioSource.volume = 0.5f; 
                audioSource.PlayOneShot(selectedClip); 
            }
        }
    }

    public void SetFacingDirection(bool facingRight)
    {
        isFacingRight = facingRight;
        firePoint.localRotation = facingRight ? Quaternion.Euler(0, 0, 0) : Quaternion.Euler(0, 180, 0);
        float scaleX = facingRight ? 1 : -1;
        swordPoint.localScale = new Vector3(scaleX, 1, 1);
    }


}
