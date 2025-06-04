using UnityEngine;

public class ArmUpperTwitch : MonoBehaviour
{
    public float angle = 10f;
    public float speed = 3f;

    void Update()
    {
        float rot = Mathf.Sin(Time.time * speed) * angle;
        transform.localRotation = Quaternion.Euler(0, 0, rot);
    }
}
