using UnityEngine;
using System.Collections;
using TMPro;
using UnityEngine.SceneManagement;
using System.Linq;

public class GameManager : MonoBehaviour
{
    [Header("Wave Management")]
    public int currentWave = 0;
    public int zombiesPerWave;
    public float spawnDelay;
    private int zombiesSpawned = 0;
    public int zombiesAlive = 0;

    [Header("Zombie Spawning")]
    public GameObject zombiePrefab;
    public GameObject jumperZombiePrefab;
    public GameObject runnerZombiePrefab;
    public GameObject bruteZombiePrefab;
    public Transform[] spawnPoints;
    private bool spawnOnRight = true; 
    public float initialSpawnDelay = 3f;

    [Range(0f, 1f)] public float jumperSpawnChance = 0.2f;
    [Range(0f, 1f)] public float runnerSpawnChance = 0.1f;
    [Range(0f, 1f)] public float bruteSpawnChance = 0.05f;
    [Range(0f, 1f)] public float regularZombieSpawnChance = 0.65f;

    [Header("Power-Up Spawning")]
    public GameObject healthPackPrefab;
    public GameObject ammoPackPrefab;
    public GameObject batteryPackPrefab;
    public float powerUpSpawnInterval = 15f;
    [Range(0f, 1f)] public float healthPackSpawnChance = 0.33f;
    [Range(0f, 1f)] public float ammoPackSpawnChance = 0.33f;
    [Range(0f, 1f)] public float batteryPackSpawnChance = 0.34f;

    [Header("UI")]
    public TextMeshProUGUI waveText;
    public GameObject gameOverScreen;
    public GameObject pauseMenu;
    public GameObject gameUI;

    [Header("Sounds")]
    private AudioSource audioSource;
    public AudioClip backgroundsound;


    private GameObject player;
    private bool isPaused = false;

    void Start()
    {
        player = GameObject.FindWithTag("Player");
        Transform spawnPointsParent = GameObject.Find("SpawnPoints")?.transform;
        if (spawnPointsParent != null)
        {
            spawnPoints = spawnPointsParent.GetComponentsInChildren<Transform>()
                                           .Where(t => t != spawnPointsParent)
                                           .ToArray();
        }

        waveText = GameObject.Find("WaveText")?.GetComponent<TextMeshProUGUI>();
        gameUI = GameObject.Find("UI HUD");

        audioSource = gameObject.AddComponent<AudioSource>();
        audioSource.clip = backgroundsound;
        audioSource.loop = true; 
        audioSource.volume = 1f; 
        audioSource.playOnAwake = true;

        audioSource.Play();

        StartNextWave();
        InvokeRepeating("SpawnPowerUp", powerUpSpawnInterval, powerUpSpawnInterval);
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            if (isPaused) ResumeGame();
            else PauseGame();
        }
    }

    void StartNextWave()
    {
        currentWave++;


        StartCoroutine(DisplayWaveTextTypewriter());

        AdjustWaveParameters();
        zombiesSpawned = 0;
        zombiesAlive = zombiesPerWave;

        InvokeRepeating("SpawnZombie", 0f, spawnDelay);

    }


    void AdjustWaveParameters()
    {
        if (currentWave < 5)
        {
            zombiesPerWave = 5 + currentWave * 2;
            spawnDelay = initialSpawnDelay - currentWave * 0.2f;
        }
        else if (currentWave < 10)
        {
            zombiesPerWave = 15 + (currentWave - 5) * 3;
            spawnDelay = Mathf.Max(1f, initialSpawnDelay - currentWave * 0.3f);
        }
        else
        {
            zombiesPerWave = Mathf.Min(30 + (currentWave - 10) * 4, 50);
            spawnDelay = Mathf.Max(0.8f, initialSpawnDelay - currentWave * 0.35f);
        }
    }

    IEnumerator DisplayWaveTextTypewriter()
    {
        string waveMessage = "WAVE: " + currentWave;
        waveText.text = "";
        waveText.gameObject.SetActive(true);

        foreach (char letter in waveMessage)
        {
            waveText.text += letter;
            yield return new WaitForSeconds(0.1f);
        }

        yield return new WaitForSeconds(1f);
        waveText.gameObject.SetActive(false);
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


    GameObject SelectZombiePrefab()
    {
        float rand = Random.Range(0f, 1f);

        if (rand <= bruteSpawnChance) return bruteZombiePrefab;
        else if (rand <= bruteSpawnChance + runnerSpawnChance) return runnerZombiePrefab;
        else if (rand <= bruteSpawnChance + runnerSpawnChance + jumperSpawnChance) return jumperZombiePrefab;
        else return zombiePrefab;
    }

    Transform GetValidSpawnPoint()
    {
        if (player == null)
        {
            return null;
        }
        float playerX = player.transform.position.x;
        Transform[] validSpawnPoints = System.Array.FindAll(spawnPoints, sp =>
            Vector2.Distance(player.transform.position, sp.position) >= 5f &&
            (spawnOnRight ? sp.position.x > playerX : sp.position.x < playerX));

        spawnOnRight = !spawnOnRight;

        return validSpawnPoints.Length > 0 ? validSpawnPoints[Random.Range(0, validSpawnPoints.Length)] : null;
    }

    public void ZombieDied()
    {
        zombiesAlive--;
        if (zombiesAlive <= 0) StartNextWave();
    }

    void SpawnPowerUp()
    {
        float rand = Random.Range(0f, 1f);
        GameObject powerUpToSpawn;

        if (rand < healthPackSpawnChance) powerUpToSpawn = healthPackPrefab;
        else if (rand < healthPackSpawnChance + ammoPackSpawnChance) powerUpToSpawn = ammoPackPrefab;
        else powerUpToSpawn = batteryPackPrefab;

        Transform spawnPoint = spawnPoints[Random.Range(0, spawnPoints.Length)];
        Instantiate(powerUpToSpawn, spawnPoint.position, Quaternion.identity);
    }

    public void PauseGame()
    {
        isPaused = true;
        Time.timeScale = 0f;

        TogglePlayerComponents(false);


        pauseMenu.SetActive(true);
        gameUI.SetActive(false);
    }

    public void ResumeGame()
    {
        isPaused = false;
        Time.timeScale = 1f;

        TogglePlayerComponents(true);


        pauseMenu.SetActive(false);
        gameUI.SetActive(true);
    }

    private void TogglePlayerComponents(bool isEnabled)
    {
        if (player != null)
        {
            var movement = player.GetComponent<PlayerMovement>();
            if (movement != null) movement.enabled = isEnabled;

            var aim = player.GetComponent<PlayerAim>();
            if (aim != null) aim.enabled = isEnabled;

            var flashlight = player.GetComponent<PlayerLight>();
            if (flashlight != null) flashlight.enabled = isEnabled;
        }
    }


    public void PlayerDied()
    {
        Time.timeScale = 0f;

        TogglePlayerComponents(false);
        gameOverScreen.SetActive(true);
        gameUI.SetActive(false);
    }


    public void RetryGame()
    {
        Time.timeScale = 1f;

        CancelInvoke();


        SceneManager.LoadScene("Arena");
    }


    public void QuitToMenu()
    {
        Time.timeScale = 1f;
        SceneManager.LoadScene("MainMenu");
    }
}
