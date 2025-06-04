using UnityEngine;

public class RobotArmController : MonoBehaviour
{
    public Transform baseJoint;         // From ArmBaseSwing
    public Transform lowerJoint;        // From ArmLowerSwing
    public Transform upperJoint;        // From ArmUpperTwitch

    public float baseSpeed = 1.5f;
    public float baseAngle = 45f;

    public float lowerSpeed = 2f;
    public float lowerAngle = 20f;

    public float upperSpeed = 3f;
    public float upperAngle = 10f;

    private Quaternion lowerStartRot;
    private Quaternion upperStartRot;
    private bool shouldStop = false;

    void Start()
    {
        if (lowerJoint) lowerStartRot = lowerJoint.localRotation;
        if (upperJoint) upperStartRot = upperJoint.localRotation;
    }

    void Update()
    {
        if (shouldStop) return;

        if (baseJoint)
        {
            float rot = Mathf.PingPong(Time.time * baseSpeed, baseAngle * 2) - baseAngle;
            transform.localRotation = Quaternion.Euler(0, rot, 0);
        }

        if (lowerJoint)
        {
            float lowerRot = Mathf.Sin(Time.time * lowerSpeed) * lowerAngle;
            lowerJoint.localRotation = lowerStartRot * Quaternion.Euler(lowerRot, 0, 0);
        }

        if (upperJoint)
        {
            float upperRot = Mathf.Sin(Time.time * upperSpeed) * upperAngle;
            upperJoint.localRotation = upperStartRot * Quaternion.Euler(0, 0, upperRot);
        }
    }

    public void StopMovement()
    {
        shouldStop = true;
    }
}
