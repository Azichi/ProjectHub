using UnityEngine;

public class ResourceManagement : MonoBehaviour
{
    public int ammoCount;
    public int healthPackCount;
    public int batteryPackCount;

    public AudioClip batterysound;
    public AudioClip reloadsound;
    public AudioClip healthsound;
    private AudioSource audioSource;


    private PlayerHealth playerHealth;


    void Start()
    {
        playerHealth = FindObjectOfType<PlayerHealth>();
        audioSource = gameObject.AddComponent<AudioSource>();
        audioSource.playOnAwake = false;
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Alpha1))
        {
            UseHealthPack();
            audioSource.PlayOneShot(healthsound);
        }

        if (Input.GetKeyDown(KeyCode.Alpha2))
        {
            UseBatteryPack();
            audioSource.PlayOneShot(batterysound);
        }
    }

    public void AddAmmo(int amount)
    {
        ammoCount += amount;
        UpdateHUD();
    }

    public void AddHealthPack(int amount)
    {
        healthPackCount += amount;
        UpdateHUD();
    }

    public void AddBatteryPack(int amount)
    {
        batteryPackCount += amount;
        UpdateHUD();
    }

    private void UseHealthPack()
    {
        if (healthPackCount > 0 && playerHealth != null)
        {
            playerHealth.RestoreHealth(20);
            healthPackCount--;
            UpdateHUD();
        }
    }

    private void UseBatteryPack()
    {
        if (batteryPackCount > 0)
        {
            batteryPackCount--;
            UpdateHUD();
        }
    }

    private void UpdateHUD()
    {
        HUDManager hudManager = FindObjectOfType<HUDManager>();
        if (hudManager != null)
        {
            hudManager.UpdateAmmo(ammoCount);
            hudManager.UpdateHealthPacks(healthPackCount);
            hudManager.UpdateBatteryPacks(batteryPackCount);
            hudManager.UpdateHealth(playerHealth.currentHealth);
        }
    }
}
