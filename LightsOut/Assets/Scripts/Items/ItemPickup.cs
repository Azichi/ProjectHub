using UnityEngine;

public class ItemPickup : MonoBehaviour
{
    public enum ItemType { Ammo, HealthPack, BatteryPack }
    public ItemType itemType;
    public int amount = 1;
    public AudioClip[] pickupsounds;
    private AudioSource audioSource;

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Player"))
        {
            ResourceManagement resourceManager = other.GetComponent<ResourceManagement>();
            if (resourceManager != null)
            {
                switch (itemType)
                {
                    case ItemType.Ammo:
                        resourceManager.AddAmmo(amount);
                        break;
                    case ItemType.HealthPack:
                        resourceManager.AddHealthPack(amount);
                        break;
                    case ItemType.BatteryPack:
                        resourceManager.AddBatteryPack(amount);
                        break;
                }

                PlayPickupSound();

                Destroy(gameObject);
            }
        }
    }

    private void PlayPickupSound()
    {
        if (pickupsounds.Length > 0)
        {
            AudioClip clip = pickupsounds[Random.Range(0, pickupsounds.Length)];

            GameObject tempAudio = new GameObject("TempAudio");
            AudioSource tempAudioSource = tempAudio.AddComponent<AudioSource>();
            tempAudioSource.clip = clip;
            tempAudioSource.playOnAwake = false;
            tempAudioSource.Play();

            Destroy(tempAudio, clip.length);
        }
    }
}
