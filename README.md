# CalitateAer Romania (RNMCA) - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/emanuelbesliu/homeassistant-calitateaer.svg)](https://github.com/emanuelbesliu/homeassistant-calitateaer/releases)
[![License](https://img.shields.io/github/license/emanuelbesliu/homeassistant-calitateaer.svg)](LICENSE)

Integrare Home Assistant pentru monitorizarea calității aerului în România folosind datele de la **Rețeaua Națională de Monitorizare a Calității Aerului (RNMCA)** prin API-ul [calitateaer.ro](https://calitateaer.ro).

## Funcționalități

- **6 senzori per poluant** per stație: PM2.5, PM10, SO2, NO2, O3, CO
- **Index general AQI** (1-6) conform legislației românești, cu icon dinamic
- **Index AQI per poluant** disponibil ca atribut pe fiecare senzor
- **Suport multi-stație** — selectezi una sau mai multe stații la configurare
- **Device grouping** — senzorii sunt grupați per stație în HA
- **Coordonate GPS** ale stației expuse ca atribute (latitude, longitude, altitude)
- **Actualizare automată** la fiecare oră (configurabil)
- **Traduceri complete** română și engleză

## Cerințe

### Credențiale API RNMCA

API-ul RNMCA necesită autentificare HTTP Basic Auth. Credențialele sunt **gratuite** și se obțin trimițând un mesaj prin [pagina de contact](https://calitateaer.ro/public/contact-page/) de pe calitateaer.ro, cu:

- Nume și prenume
- Adresa de email
- Motivul cererii accesului la API
- Modulul/modulele dorite (Simplified Data API + Air Quality Index API)
- Limba datelor (Română sau Engleză)

## Instalare

### HACS (Recomandat)

1. Deschide **HACS** în Home Assistant
2. Click pe **Integrations**
3. Click pe meniul cu 3 puncte → **Custom repositories**
4. Adaugă URL: `https://github.com/emanuelbesliu/homeassistant-calitateaer`
5. Categorie: **Integration**
6. Caută **CalitateAer Romania** și instalează
7. Repornește Home Assistant

### Instalare manuală

```bash
cd /config/custom_components
git clone https://github.com/emanuelbesliu/homeassistant-calitateaer.git
cp -r homeassistant-calitateaer/custom_components/calitateaer .
rm -rf homeassistant-calitateaer
```

Repornește Home Assistant.

## Configurare

1. **Settings → Devices & Services → Add Integration**
2. Caută **CalitateAer Romania (RNMCA)**
3. Introduceți **username** și **password** (credențialele API obținute de la RNMCA)
4. Selectați **stația/stațiile de monitorizare** din lista încărcată automat
5. Done! Senzorii vor apărea automat

### Opțiuni

După configurare, puteți modifica intervalul de actualizare:

- **Settings → Devices & Services → CalitateAer → Configure**
- **Interval actualizare**: 600 - 86400 secunde (implicit: 3600 = 1 oră)

## Senzori creați

Pentru fiecare stație selectată se creează următorii senzori:

| Senzor | Tip | Unitate | Descriere |
|--------|-----|---------|-----------|
| Index Calitate Aer | AQI | - | Index general 1-6 (Bun → Extrem de slab) |
| PM2.5 | Concentrație | µg/m³ | Particule fine < 2.5 µm |
| PM10 | Concentrație | µg/m³ | Particule în suspensie < 10 µm |
| SO2 | Concentrație | µg/m³ | Dioxid de sulf |
| NO2 | Concentrație | µg/m³ | Dioxid de azot |
| O3 | Concentrație | µg/m³ | Ozon |
| CO | Concentrație | mg/m³ | Monoxid de carbon |

### Atribute senzori

Fiecare senzor de poluant include:
- `station_name`, `station_code`, `network`
- `measurement_time`, `averaging_period`
- `aqi_level`, `aqi_label` (index AQI specific poluantului)

Senzorul AQI general include adițional:
- `latitude`, `longitude`, `altitude`
- Index AQI per poluant: `PM2.5_aqi`, `PM10_aqi`, etc.

### Niveluri AQI (conform legislației românești)

| Index | Nivel | Descriere |
|-------|-------|-----------|
| 1 | Bun | Calitatea aerului este satisfăcătoare |
| 2 | Acceptabil | Calitatea aerului este acceptabilă |
| 3 | Moderat | Grupuri sensibile pot fi afectate |
| 4 | Slab | Efecte asupra sănătății posibile |
| 5 | Foarte slab | Efecte negative asupra sănătății |
| 6 | Extrem de slab | Condiții de urgență |

## Exemple de automatizări

### Alertă când AQI depășește nivelul "Moderat"

```yaml
alias: "Alertă Calitate Aer Slabă"
description: >-
  Trimite notificare când indexul calității aerului depășește nivelul Moderat (3).
mode: single
max_exceeded: silent

triggers:
  - entity_id: sensor.calitateaer_statia_x_index_calitate_aer
    above: 3
    trigger: numeric_state

actions:
  - action: notify.mobile_app_telefon
    data:
      title: "Calitate Aer Slabă"
      message: >-
        Indexul calității aerului la stația {{ state_attr('sensor.calitateaer_statia_x_index_calitate_aer', 'station_name') }}
        este {{ states('sensor.calitateaer_statia_x_index_calitate_aer') }}
        ({{ state_attr('sensor.calitateaer_statia_x_index_calitate_aer', 'aqi_label') }}).
```

### Alertă PM2.5 ridicat

```yaml
alias: "Alertă PM2.5 Ridicat"
description: >-
  Trimite notificare când PM2.5 depășește 25 µg/m³.
mode: single
max_exceeded: silent

triggers:
  - entity_id: sensor.calitateaer_statia_x_pm2_5
    above: 25
    trigger: numeric_state

actions:
  - action: notify.mobile_app_telefon
    data:
      title: "PM2.5 Ridicat"
      message: >-
        Concentrația PM2.5 este {{ states('sensor.calitateaer_statia_x_pm2_5') }} µg/m³.
```

## Despre RNMCA

**Rețeaua Națională de Monitorizare a Calității Aerului (RNMCA)** este administrată de Agenția Națională pentru Protecția Mediului (ANPM) și cuprinde peste 100 de stații de monitorizare pe teritoriul României. Datele sunt actualizate orar și sunt disponibile prin API-ul public de la [calitateaer.ro](https://calitateaer.ro).

## Suport

- [GitHub Issues](https://github.com/emanuelbesliu/homeassistant-calitateaer/issues)
- [HACS](https://hacs.xyz/)

## Licență

Acest proiect este distribuit sub licența MIT. Vezi fișierul [LICENSE](LICENSE) pentru detalii.
