using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class UDPVestReceiver : MonoBehaviour
{
    public ControlLogic controlLogic;
    private UdpClient client;
    private Thread receiveThread;
    private bool running = true;

    void Start()
    {
        client = new UdpClient(5005);
        receiveThread = new Thread(ReceiveData);
        receiveThread.IsBackground = true;
        receiveThread.Start();
    }

    void ReceiveData()
    {
        IPEndPoint anyIP = new IPEndPoint(IPAddress.Any, 0);
        while (running)
        {
            try
            {
                byte[] data = client.Receive(ref anyIP);
                string message = Encoding.UTF8.GetString(data).Trim();

                bool isVest = message == "1";
                controlLogic.vestDetected = isVest;
            }
            catch { }
        }
    }

    void OnApplicationQuit()
    {
        running = false;
        receiveThread?.Abort();
        client?.Close();
    }
}
