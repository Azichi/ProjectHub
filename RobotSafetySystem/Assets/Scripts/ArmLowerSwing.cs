using UnityEngine;

public class ArmLowerSwing : MonoBehaviour
{
    public float angle = 20f;
    public float speed = 2f;

    void Update()
    {
        float rot = Mathf.Sin(Time.time * speed) * angle;
        transform.localRotation = Quaternion.Euler(rot, 0, 0);
    }
}
