using UnityEngine;
using System.Net.Sockets;
using System.Net;
using System.IO;

public class UdpImageSender : MonoBehaviour
{
    public string ip = "127.0.0.1";
    public int port = 5050;
    public Camera sourceCamera;
    public int captureWidth = 320;
    public int captureHeight = 240;
    public float sendInterval = 0.1f;

    private UdpClient client;
    private RenderTexture rt;
    private Texture2D tex;
    private float timer;

    void Start()
    {
        client = new UdpClient();
        rt = new RenderTexture(captureWidth, captureHeight, 24);
        tex = new Texture2D(captureWidth, captureHeight, TextureFormat.RGB24, false);
    }

    void Update()
    {
        timer += Time.deltaTime;
        if (timer >= sendInterval)
        {
            timer = 0f;

            RenderTexture.active = rt;
            sourceCamera.targetTexture = rt;
            sourceCamera.Render();
            tex.ReadPixels(new Rect(0, 0, captureWidth, captureHeight), 0, 0);
            tex.Apply();
            sourceCamera.targetTexture = null;
            RenderTexture.active = null;

            byte[] jpg = tex.EncodeToJPG(50);
            client.Send(jpg, jpg.Length, ip, port);
        }
    }

    void OnApplicationQuit()
    {
        client.Close();
    }
}
