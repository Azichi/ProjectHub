using UnityEngine;

public class ArmBaseSwing : MonoBehaviour
{
    public float angle = 45f;
    public float speed = 1.5f;

    void Update()
    {
        float rot = Mathf.PingPong(Time.time * speed, angle * 2) - angle;
        transform.localRotation = Quaternion.Euler(0, rot, 0);
    }
}
