using UnityEngine;
using TMPro;

public class HUDManager : MonoBehaviour
{
    public TextMeshProUGUI healthText;
    public TextMeshProUGUI ammoText;
    public TextMeshProUGUI waveText;
    public TextMeshProUGUI countdownText;
    public TextMeshProUGUI healthPackText;
    public TextMeshProUGUI batteryPackText;

    private PlayerHealth playerHealth;
    private ResourceManagement resourceManager;
    private GameManager arenaManager;
    private CampaignManager campaignManager;

    public AudioClip spawnSound;
    private AudioSource audioSource;

    void Start()
    {
        playerHealth = FindObjectOfType<PlayerHealth>();
        resourceManager = FindObjectOfType<ResourceManagement>();
        audioSource = gameObject.AddComponent<AudioSource>();
        audioSource.volume = 0.5f;
        arenaManager = FindObjectOfType<GameManager>();
        campaignManager = FindObjectOfType<CampaignManager>();


        PlaySpawnSound();
    }
    void Update2()
    {
        if (arenaManager != null)
        {
            waveText.gameObject.SetActive(true);
            countdownText.gameObject.SetActive(true);

            waveText.text = "Wave: " + arenaManager.currentWave;
            countdownText.text = "Zombies Alive: " + arenaManager.zombiesAlive;
        }
        else if (campaignManager != null)
        {
            waveText.gameObject.SetActive(false);
            countdownText.gameObject.SetActive(false);

        }
    }

    void Update()
    {
        if (playerHealth != null)
            healthText.text = "Health: " + playerHealth.currentHealth;

        if (resourceManager != null)
        {
            ammoText.text = "Ammo: " + resourceManager.ammoCount;
            healthPackText.text = "" + resourceManager.healthPackCount;
            batteryPackText.text = "" + resourceManager.batteryPackCount;
        }

        if (arenaManager != null)
        {
            waveText.text = "Wave: " + arenaManager.currentWave;
            countdownText.text = "Zombies Alive: " + arenaManager.zombiesAlive;
        }
    }

    public void UpdateHealthPacks(int healthPackCount)
    {
        healthPackText.text = "" + healthPackCount;
    }

    public void UpdateBatteryPacks(int batteryPackCount)
    {
        batteryPackText.text = "" + batteryPackCount;
    }
    public void UpdateAmmo(int ammoCount)
    {
        ammoText.text = "Ammo: " + ammoCount;
    }

    public void UpdateHealth(int currentHealth)
    {
        healthText.text = "Health: " + currentHealth;
    }

    public void PlaySpawnSound()
    {
        if (spawnSound != null && audioSource != null)
        {
            audioSource.PlayOneShot(spawnSound);
        }
    }

}
