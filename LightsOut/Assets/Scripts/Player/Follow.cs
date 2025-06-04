using UnityEngine;

public class CameraFollow : MonoBehaviour
{
    public Transform target;  
    public float smoothSpeed = 0.125f;  
    public Vector3 offset = new Vector3(0, 0, -10);  
    public float lockedYPosition = -1f; 

    public float shakeDuration = 0.1f; 
    public float shakeMagnitude = 0.1f;

    private Vector3 initialPosition;

    void LateUpdate()
    {
        if (target != null)
        {
            Vector3 desiredPosition = new Vector3(target.position.x, target.position.y, offset.z);
            Vector3 smoothedPosition = Vector3.Lerp(transform.position, desiredPosition, smoothSpeed);
            transform.position = smoothedPosition;
        }
    }

    public void TriggerShake()
    {
        StartCoroutine(Shake());
    }

    private System.Collections.IEnumerator Shake()
    {
        initialPosition = transform.position;

        float elapsed = 0.0f;
        while (elapsed < shakeDuration)
        {
            float offsetX = Random.Range(-1f, 1f) * shakeMagnitude;
            float offsetY = Random.Range(-1f, 1f) * shakeMagnitude;

            transform.position = new Vector3(initialPosition.x + offsetX, initialPosition.y + offsetY, initialPosition.z);

            elapsed += Time.deltaTime;

            yield return null;
        }

        transform.position = initialPosition;
    }
}
