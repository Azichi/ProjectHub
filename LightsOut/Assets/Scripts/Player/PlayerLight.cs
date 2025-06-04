using UnityEngine;
using UnityEngine.Rendering.Universal; 

public class PlayerLight : MonoBehaviour
{
    public Light2D playerLight;
    public float batteryLife = 100f;
    public float batteryDrainRate = 1f; 

    void Update()
    {
        if (batteryLife > 0)
        {
            batteryLife -= batteryDrainRate * Time.deltaTime;
        }
        else
        {
            playerLight.enabled = false; 
        }
    }
}
