using UnityEngine;
using UnityEngine.SceneManagement;

public class MainMenu : MonoBehaviour
{
    public GameObject campaignButton; 
    public GameObject arenaButton;    
    public GameObject easyButton;     
    public GameObject mediumButton;    
    public GameObject hardButton;      

    private string selectedMode = "Arena"; 

    void Start()
    {
        easyButton.SetActive(false);
        mediumButton.SetActive(false);
        hardButton.SetActive(false);
    }

    public void OnCampaignModeButtonClicked()
    {
        selectedMode = "Campaign";
        ShowDifficultyButtons();
    }

    public void OnArenaModeButtonClicked()
    {
        selectedMode = "Arena";
        ShowDifficultyButtons();
    }

    public void OnEasyButtonClicked()
    {
        LoadSelectedModeWithDifficulty("Easy");
    }

    public void OnMediumButtonClicked()
    {
        LoadSelectedModeWithDifficulty("Medium");
    }

    public void OnHardButtonClicked()
    {
        LoadSelectedModeWithDifficulty("Hard");
    }

    private void ShowDifficultyButtons()
    {
        campaignButton.SetActive(false);
        arenaButton.SetActive(false);

        easyButton.SetActive(true);
        mediumButton.SetActive(true);
        hardButton.SetActive(true);
    }

    private void LoadSelectedModeWithDifficulty(string difficulty)
    {
        PlayerPrefs.SetString("Difficulty", difficulty);

        if (selectedMode == "Campaign")
        {
            SceneManager.LoadScene("Level1"); 
        }
        else if (selectedMode == "Arena")
        {
            SceneManager.LoadScene("Arena");
        }
    }
}
