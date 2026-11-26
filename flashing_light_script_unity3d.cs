using UnityEngine;

public class LuzDestellante : MonoBehaviour
{
    private Light luz;
    
    [Header("Configuración del Destello")]
    [Tooltip("Tiempo que la luz permanece encendida")]
    public float tiempoEncendido = 0.5f;
    
    [Tooltip("Tiempo que la luz permanece apagada")]
    public float tiempoApagado = 0.5f;

    private float cronometro = 0f;

    void Start()
    {
        // Obtenemos el componente Light del objeto
        luz = GetComponent<Light>();
        
        if (luz == null)
        {
            Debug.LogError("No se encontró un componente Light en este objeto: " + gameObject.name);
        }
    }

    void Update()
    {
        if (luz == null) return;

        cronometro += Time.deltaTime;

        if (luz.enabled)
        {
            // Si está encendida y pasa el tiempo, se apaga
            if (cronometro >= tiempoEncendido)
            {
                luz.enabled = false;
                cronometro = 0f;
            }
        }
        else
        {
            // Si está apagada y pasa el tiempo, se enciende
            if (cronometro >= tiempoApagado)
            {
                luz.enabled = true;
                cronometro = 0f;
            }
        }
    }
}