using UnityEngine;

public class ZombieSpawner : MonoBehaviour
{
    [Header("Zombie Settings")]
    public GameObject zombiePrefab;
    public float proximityRadius = 5f;
    public bool spawnOnlyOnce = true;
    private bool hasSpawned = false;

    private GameObject player;

    void Start()
    {
        player = GameObject.FindWithTag("Player");
    }

    void Update()
    {
        if (player == null || hasSpawned && spawnOnlyOnce) return;

        float distance = Vector3.Distance(player.transform.position, transform.position);
        if (distance <= proximityRadius)
        {
            SpawnZombie();
        }
    }

    private void SpawnZombie()
    {
        if (zombiePrefab != null)
        {
            Instantiate(zombiePrefab, transform.position, Quaternion.identity);

            if (spawnOnlyOnce) hasSpawned = true;
        }
    }
}
