using UnityEngine;

public class DifficultyManager : MonoBehaviour
{
    public static DifficultyManager Instance;

    public float healthMultiplier = 1.0f;
    public float speedMultiplier = 1.0f;
    public float damageMultiplier = 1.0f;

    private void Awake()
    {
        if (Instance == null)
        {
            Instance = this;
            //DontDestroyOnLoad(gameObject);
        }
        else
        {
            Destroy(gameObject);
        }

        string savedDifficulty = PlayerPrefs.GetString("Difficulty", "Medium"); 
        SetDifficulty(savedDifficulty);
    }

    public void SetDifficulty(string difficulty)
    {
        switch (difficulty)
        {
            case "Easy":
                healthMultiplier = 0.8f;
                speedMultiplier = 0.8f;
                damageMultiplier = 0.8f;
                break;

            case "Medium":
                healthMultiplier = 1.0f;
                speedMultiplier = 1.0f;
                damageMultiplier = 1.0f;
                break;

            case "Hard":
                healthMultiplier = 1.5f;
                speedMultiplier = 1.5f;
                damageMultiplier = 1.5f;
                break;

            default:
                healthMultiplier = 1.0f;
                speedMultiplier = 1.0f;
                damageMultiplier = 1.0f;
                break;
        }

    }
}
