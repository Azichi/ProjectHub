using UnityEngine;

public class CampaignManager : MonoBehaviour
{
    [Header("Zombie Spawning")]
    public GameObject zombiePrefab;
    public GameObject jumperZombiePrefab;
    public GameObject runnerZombiePrefab;
    public GameObject bruteZombiePrefab;

    [System.Serializable]
    public class ZombieSpawnPoint
    {
        public Transform spawnPoint;
        public GameObject zombieType; 
        public float spawnDelay;
    }

    public ZombieSpawnPoint[] zombieSpawnPoints; 

    private GameObject player;

    [Header("UI")]
    public GameObject gameOverScreen;
    public GameObject pauseMenu;
    public GameObject gameUI;

    [Header("Sounds")]
    private AudioSource audioSource;
    public AudioClip backgroundsound;

    private bool isPaused = false;

    void Start()
    {
        player = GameObject.FindWithTag("Player");

        audioSource = gameObject.AddComponent<AudioSource>();
        audioSource.clip = backgroundsound;
        audioSource.loop = true;
        audioSource.volume = 1f;
        audioSource.Play();

        foreach (var spawnPoint in zombieSpawnPoints)
        {
            StartCoroutine(SpawnZombieAtLocation(spawnPoint));
        }
    }

    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            if (isPaused) ResumeGame();
            else PauseGame();
        }
    }

    private System.Collections.IEnumerator SpawnZombieAtLocation(ZombieSpawnPoint spawnPoint)
    {
        yield return new WaitForSeconds(spawnPoint.spawnDelay);

        if (spawnPoint.zombieType != null && spawnPoint.spawnPoint != null)
        {
            GameObject newZombie = Instantiate(spawnPoint.zombieType, spawnPoint.spawnPoint.position, Quaternion.identity);

            ZombieAI zombieAI = newZombie.GetComponent<ZombieAI>();
            if (zombieAI != null) zombieAI.player = player.transform;
        }
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
        Debug.Log("Game Over!");
        Time.timeScale = 0f;

        TogglePlayerComponents(false);
        gameOverScreen.SetActive(true);
        gameUI.SetActive(false);
    }

    public void RetryGame()
    {
        Time.timeScale = 1f;
        TogglePlayerComponents(true);
        UnityEngine.SceneManagement.SceneManager.LoadScene(UnityEngine.SceneManagement.SceneManager.GetActiveScene().name);
    }

    public void QuitToMenu()
    {
        Time.timeScale = 1f;
        UnityEngine.SceneManagement.SceneManager.LoadScene("MainMenu");
    }
}
