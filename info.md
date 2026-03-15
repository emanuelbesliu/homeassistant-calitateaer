# CalitateAer - Integrare Home Assistant

Integrare pentru monitorizarea calității aerului în România folosind datele de la **Rețeaua Națională de Monitorizare a Calității Aerului (RNMCA)** prin API-ul calitateaer.ro.

## Funcționalități

- Monitorizare în timp real a poluanților: PM2.5, PM10, SO2, NO2, O3, CO
- Index general al calității aerului (AQI) conform legislației românești
- Suport pentru peste 100 de stații de monitorizare din România
- Actualizare automată la fiecare oră
- Traduceri complete română/engleză

## Instalare

### HACS (Recomandat)

1. Deschide HACS în Home Assistant
2. Click pe "Integrations"
3. Click pe meniul cu 3 puncte → "Custom repositories"
4. Adaugă: `https://github.com/emanuelbesliu/homeassistant-calitateaer`
5. Categorie: "Integration"
6. Caută "CalitateAer Romania" și instalează

### Manual

```bash
cd /config/custom_components
git clone https://github.com/emanuelbesliu/homeassistant-calitateaer.git calitateaer
mv calitateaer/custom_components/calitateaer/* calitateaer/
rm -rf calitateaer/custom_components
```

## Configurare

1. Obțineți credențiale API de la RNMCA (email de contact pe calitateaer.ro)
2. Reporniți Home Assistant
3. **Settings → Devices & Services → Add Integration**
4. Căutați "CalitateAer Romania"
5. Introduceți username-ul și parola API
6. Selectați stația/stațiile de monitorizare dorite

## Documentație Completă

Vezi [README complet](README.md) pentru:
- Instrucțiuni detaliate de instalare
- Exemple de automatizări
- Configurare dashboard
- Troubleshooting

## Support

- [GitHub Issues](https://github.com/emanuelbesliu/homeassistant-calitateaer/issues)
- [Documentație completă](README.md)
