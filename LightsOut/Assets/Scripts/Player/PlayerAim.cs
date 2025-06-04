using UnityEngine;

public class PlayerAim : MonoBehaviour
{
    public Transform firepoint; 
    public Transform gun; 

    private Vector3 originalScale; 
    private Vector3 gunOriginalScale;
    private Vector3 gunOriginalPosition;

    public Vector3 leftFacingOffset = new Vector3(-0.2f, 0, 0); 

    void Start()
    {
        originalScale = transform.localScale;
        gunOriginalScale = gun.localScale;
        gunOriginalPosition = gun.localPosition;
    }

    void Update()
    {
        AimAndFlip();
    }

    void AimAndFlip()
    {
        Vector3 mousePosition = Camera.main.ScreenToWorldPoint(Input.mousePosition);
        mousePosition.z = transform.position.z; 

        Vector3 aimDirection = (mousePosition - firepoint.position).normalized;
        float aimAngle = Mathf.Atan2(aimDirection.y, aimDirection.x) * Mathf.Rad2Deg;

        firepoint.rotation = Quaternion.Euler(0, 0, aimAngle);

        if (aimDirection.x < 0)
        {
            transform.localScale = new Vector3(-Mathf.Abs(originalScale.x), originalScale.y, originalScale.z);

            gun.localScale = new Vector3(gunOriginalScale.x, -Mathf.Abs(gunOriginalScale.y), gunOriginalScale.z);

            gun.localPosition = gunOriginalPosition + leftFacingOffset;
        }
        else
        {
            transform.localScale = originalScale;

            gun.localScale = gunOriginalScale;
            gun.localPosition = gunOriginalPosition;
        }
    }
}
