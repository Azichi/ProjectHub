using UnityEngine;

public class ControlLogic : MonoBehaviour
{
    public RobotArmController robotArm; 

    // Inputs
    public bool systemActive = true;
    public bool vestDetected = false;
    public bool characterInDangerZone = false;

    private bool hasStopped = false;

    void Update()
    {
        // PLC control logic
        if (systemActive && vestDetected && characterInDangerZone)
        {
            if (!hasStopped)
            {
                robotArm.StopMovement();
                hasStopped = true;
            }
        }
    }
}
