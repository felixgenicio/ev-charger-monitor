# EV Charger Monitor — Cadrete

Monitoriza el estado y el historial de uso de los cargadores públicos de la red Enel X instalados en Cadrete (Zaragoza).

Consulta el estado en tiempo real de cada conector, visualiza la ocupación de las últimas 24 horas y analiza patrones de uso e historial de precios de los últimos 90 días.

## Características

- **Estado en tiempo real** de cada conector (disponible / ocupado / fuera de servicio)
- **Barra de ocupación** de las últimas 24 horas
- **Heatmap** de ocupación por hora del día para los últimos 90 días
- **Gráfica de evolución de precios** (€/kWh) por conector
- Página web estática, sin dependencias de servidor
- Actualización automática cada 5 minutos vía cron

## Requisitos

- Python 3.9+
- Acceso a internet para consultar la API de Enel X

## Instalación

```bash
git clone https://github.com/felixgenicio/ev-charger-monitor.git
cd ev-charger-monitor
```

Copia el fichero de ejemplo y rellena los IDs de los cargadores:

```bash
cp .env.example .env
```

Edita `.env` con los IDs de las estaciones:

```
CHARGER_1_ID=XXXXXXXXXXXXXXXX
CHARGER_2_ID=XXXXXXXXXXXXXXXX
```

Ejecuta el script de setup, que crea el entorno virtual, instala dependencias y registra el cron:

```bash
./setup.sh
```

## Uso

Sirve la carpeta del proyecto con cualquier servidor HTTP estático:

```bash
python3 -m http.server 8080
```

Abre [http://localhost:8080](http://localhost:8080) en el navegador.

El script `fetch_chargers.py` se ejecuta automáticamente cada 5 minutos gracias al cron registrado por `setup.sh`. También puedes lanzarlo manualmente:

```bash
.venv/bin/python fetch_chargers.py
```

## Estructura

```
ev-charger-monitor/
├── fetch_chargers.py   # Script de recolección de datos
├── index.html          # Dashboard web estático
├── setup.sh            # Setup del entorno y registro de cron
├── requirements.txt    # Dependencias Python
├── .env                # IDs de los cargadores (no commiteado)
├── .env.example        # Plantilla de configuración
└── data/               # Datos generados (no commiteado)
    ├── chargers.json   # Estado actual + historial
    └── token.json      # Token de sesión cacheado
```

## Funcionamiento interno

El script autentica contra la API pública de Enel X como usuario anónimo, obtiene el estado de cada estación y lo almacena en `data/chargers.json`. El historial conserva hasta **25.920 entradas** (90 días a intervalos de 5 minutos). El token de sesión se renueva automáticamente cuando expira.

La página web carga el JSON directamente desde el navegador y se refresca sola cada 5 minutos.
