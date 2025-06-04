using UnityEngine;

public class ZoneTrigger : MonoBehaviour
{
    public ControlLogic controlLogic;

    void OnTriggerEnter(Collider other)
    {
        if (other.CompareTag("Worker"))
        {
            controlLogic.characterInDangerZone = true;
        }
    }

    void OnTriggerExit(Collider other)
    {
        if (other.CompareTag("Worker"))
        {
            controlLogic.characterInDangerZone = false;
        }
    }
}
