using UnityEngine;

public class WalkToTargetX : MonoBehaviour
{
    public float speed = 2f;
    public float targetX = -230f;

    void Update()
    {
        if (transform.position.x > targetX)
        {
            transform.position += Vector3.left * speed * Time.deltaTime;
        }
    }
}
