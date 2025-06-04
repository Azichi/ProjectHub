using UnityEngine;
using System.Collections;
using TMPro;



public class SpawnManager : MonoBehaviour
{
    public GameObject zombiePrefab;
    public GameObject jumperZombiePrefab;
    public GameObject runnerZombiePrefab;
    public GameObject bruteZombiePrefab;
    public Transform[] spawnPoints;
    public float initialSpawnDelay = 3f;
    private GameObject player;
    public int currentWave = 1;
    private int zombiesPerWave;
    private float spawnDelay;
    public TextMeshProUGUI waveText;


    [Range(0f, 1f)] public float jumperSpawnChance = 0.2f;
    [Range(0f, 1f)] public float runnerSpawnChance = 0.1f;
    [Range(0f, 1f)] public float bruteSpawnChance = 0.05f;
    [Range(0f, 1f)] public float regularZombieSpawnChance = 0.65f;

    public float minSpawnDistanceFromPlayer = 5f;

    private int zombiesSpawned = 0;
    public int zombiesAlive = 0;

    public GameObject healthPackPrefab;
    public GameObject ammoPackPrefab;
    public GameObject batteryPackPrefab;
    public float powerUpSpawnInterval = 15f;

    [Range(0f, 1f)] public float healthPackSpawnChance = 0.33f;
    [Range(0f, 1f)] public float ammoPackSpawnChance = 0.33f;
    [Range(0f, 1f)] public float batteryPackSpawnChance = 0.34f;

    private bool spawnOnRight = true;

    void Start()
    {
        player = GameObject.FindWithTag("Player");
        StartNextWave();

        InvokeRepeating("SpawnPowerUp", powerUpSpawnInterval, powerUpSpawnInterval);
    }

    IEnumerator DisplayWaveTextTypewriter()
    {
        string waveMessage = "WAVE: " + currentWave;
        waveText.text = "";
        waveText.gameObject.SetActive(true);

        foreach (char letter in waveMessage)
        {
            waveText.text += letter;
            yield return new WaitForSeconds(0.1f); // Delay between each letter
        }

        yield return new WaitForSeconds(1f); // Keep text visible for 1 second
        waveText.gameObject.SetActive(false);
    }

    void StartNextWave()
    {
        // Display wave announcement
        StartCoroutine(DisplayWaveTextTypewriter());

        // Adjust wave parameters based on difficulty tiers
        SetWaveDifficulty(currentWave);

        // Reset zombie counters
        zombiesSpawned = 0;
        zombiesAlive = zombiesPerWave;

        // Start spawning zombies
        InvokeRepeating("SpawnZombie", 0f, spawnDelay);
    }

    void DisplayWaveAnnouncement()
    {
        waveText.text = "WAVE: " + currentWave;
        waveText.gameObject.SetActive(true);
        StartCoroutine(FadeWaveText());
        Invoke("HideWaveAnnouncement", 2f); // Hide after 2 seconds
    }

    IEnumerator FadeWaveText()
    {
        waveText.color = new Color(waveText.color.r, waveText.color.g, waveText.color.b, 1); // Fully visible
        yield return new WaitForSeconds(1f); // Keep it visible for 1 second

        for (float t = 1f; t > 0; t -= Time.deltaTime)
        {
            waveText.color = new Color(waveText.color.r, waveText.color.g, waveText.color.b, t);
            yield return null;
        }

        waveText.gameObject.SetActive(false);
    }

    void HideWaveAnnouncement()
    {
        waveText.gameObject.SetActive(false);
    }

    void SetWaveDifficulty(int wave)
    {
        if (wave < 5)
        {
            // Easy Tier (Waves 1-4)
            zombiesPerWave = 5 + wave * 2;
            spawnDelay = initialSpawnDelay - wave * 0.2f;
        }
        else if (wave < 10)
        {
            // Medium Tier (Waves 5-9)
            zombiesPerWave = 15 + (wave - 5) * 3;
            spawnDelay = Mathf.Max(1f, initialSpawnDelay - wave * 0.3f);
        }
        else
        {
            // Hard Tier (Waves 10-15, capped at 50 zombies)
            zombiesPerWave = Mathf.Min(30 + (wave - 10) * 4, 50);
            spawnDelay = Mathf.Max(0.8f, initialSpawnDelay - wave * 0.35f);
        }
    }


    void SpawnZombie()
    {
        if (zombiesSpawned >= zombiesPerWave)
        {
            CancelInvoke("SpawnZombie");
            return;
        }

        Transform spawnPoint = GetValidSpawnPoint();
        if (spawnPoint == null)
        {
            Debug.LogWarning("No valid spawn points found far enough from the player.");
            return;
        }

        GameObject newZombie = zombiePrefab;

        float rand = Random.Range(0f, 1f);

        if (rand <= bruteSpawnChance)
        {
            newZombie = Instantiate(bruteZombiePrefab, spawnPoint.position, Quaternion.identity);
        }
        else if (rand <= bruteSpawnChance + runnerSpawnChance)
        {
            newZombie = Instantiate(runnerZombiePrefab, spawnPoint.position, Quaternion.identity);
        }
        else if (rand <= bruteSpawnChance + runnerSpawnChance + jumperSpawnChance)
        {
            newZombie = Instantiate(jumperZombiePrefab, spawnPoint.position, Quaternion.identity);
        }
        else
        {
            newZombie = Instantiate(zombiePrefab, spawnPoint.position, Quaternion.identity);
        }

        ZombieAI zombieAI = newZombie.GetComponent<ZombieAI>();
        if (zombieAI != null)
            zombieAI.player = player.transform;

        zombiesSpawned++;
    }

    Transform GetValidSpawnPoint()
    {
        // Alternate spawn side
        float playerX = player.transform.position.x;
        Transform[] sideSpawnPoints = System.Array.FindAll(spawnPoints, spawnPoint =>
            spawnOnRight ? spawnPoint.position.x > playerX : spawnPoint.position.x < playerX);

        sideSpawnPoints = System.Array.FindAll(sideSpawnPoints, spawnPoint =>
            Vector2.Distance(player.transform.position, spawnPoint.position) >= minSpawnDistanceFromPlayer);

        spawnOnRight = !spawnOnRight;

        if (sideSpawnPoints.Length > 0)
        {
            return sideSpawnPoints[Random.Range(0, sideSpawnPoints.Length)];
        }

        return null;
    }

    void SpawnPowerUp()
    {
        float rand = Random.Range(0f, 1f);

        GameObject powerUpToSpawn;
        if (rand < healthPackSpawnChance)
        {
            powerUpToSpawn = healthPackPrefab;
        }
        else if (rand < healthPackSpawnChance + ammoPackSpawnChance)
        {
            powerUpToSpawn = ammoPackPrefab;
        }
        else
        {
            powerUpToSpawn = batteryPackPrefab;
        }

        Transform spawnPoint = spawnPoints[Random.Range(0, spawnPoints.Length)];
        Instantiate(powerUpToSpawn, spawnPoint.position, Quaternion.identity);
    }

    public void ZombieDefeated()
    {
        zombiesAlive--;

        if (zombiesAlive <= 0)
        {
            currentWave++;
            StartNextWave();
        }
    }

    IEnumerator SpawnEffect()
    {
        float scaleMultiplier = 1.5f; // Makes the spawn noticeable
        Vector3 originalScale = transform.localScale;
        transform.localScale = originalScale * scaleMultiplier;

        yield return new WaitForSeconds(0.2f); // Duration of the spawn effect
        transform.localScale = originalScale;
    }

}
