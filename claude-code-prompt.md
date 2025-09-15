# Claude Code Prompt: Vytvorenie Kodi Cloud Sync Addon-u

## Úvod a cieľ
Potrebujem vytvoriť Kodi service addon, ktorý bude kombinovať funkcionalitu existujúceho `service.watchedsync` addon-u s cloud synchronizáciou cez Google Drive alebo OneDrive. Addon má umožniť obojsmernú synchronizáciu medzi viacerými Kodi zariadeniami.

## Požiadavky na funkcionalitu

### Základné funkcionalité:
1. **Service addon** - automaticky sa spúšťa pri štarte Kodi
2. **Real-time synchronizácia** watched statusu a resume points (podobne ako service.watchedsync)
3. **Cloud storage podpora** pre Google Drive a OneDrive
4. **Konfigurovateľné nastavenia** - používateľ si vyberie čo synchronizovať
5. **Obojsmerná synchronizácia** - zmeny sa propagujú vo všetkých smeroch

### Čo synchronizovať (konfigurovateľné):
- `watched status` (sledované filmy/seriály)
- `resume points` (pozície prehrávania)
- `favourites.xml` (obľúbené položky)
- `sources.xml` (zdroje médií)
- `playlists` (playlisty)
- `addon nastavenia` (vybrané addon nastavenia)

### Cloud provideri:
- **Google Drive** (primárny)
- **OneDrive** (sekundárny)
- Možnosť rozšírenia o ďalších (Dropbox, atď.)

## Technické požiadavky

### Štruktúra addon-u:
```
service.cloudsync/
├── addon.xml               # Metadata a konfigurácia
├── service.py              # Hlavný service script
├── addon.py                # Entry point pre nastavenia
├── icon.png                # 256x256 ikona
├── fanart.jpg              # 1920x1080 background
├── LICENSE.txt             # GPL v3 licencia
├── changelog.txt           # História zmien
├── resources/
│   ├── settings.xml        # Konfiguračné nastavenia pre užívateľa
│   ├── language/
│   │   └── resource.language.en_gb/
│   │       └── strings.po  # Preklady
│   └── lib/
│       ├── __init__.py
│       ├── cloud_providers/
│       │   ├── __init__.py
│       │   ├── base_provider.py
│       │   ├── googledrive_provider.py
│       │   └── onedrive_provider.py
│       ├── sync_manager.py
│       ├── database_monitor.py
│       ├── file_monitor.py
│       └── utils.py
```

### Kľúčové komponenty:

#### 1. addon.xml
- Extension point: `xbmc.service`
- Python verzia kompatibilná s Kodi 19+
- Dependencie na potrebné moduly
- Správne metadata

#### 2. service.py
- Hlavný service loop s `xbmc.Monitor`
- Automatický štart pri spustení Kodi
- Graceful shutdown pri ukončení Kodi
- Thread-safe operácie

#### 3. Cloud providers
- **Google Drive API** integrácia s OAuth2
- **OneDrive API** integrácia
- Abstraktná base class pre ľahké rozšírenie
- Rate limiting a error handling

#### 4. Sync manager
- Konflikt resolution stratégie
- Incremental sync (len zmeny)
- Checksum based change detection
- Queue system pre batch operácie

#### 5. Database monitoring
- Sledovanie Kodi databázy zmien (MyVideos, MyMusic)
- JSON-RPC API využitie pre získanie informácií
- Real-time detection watched status changes

#### 6. File monitoring
- Sledovanie zmien v userdata súboroch
- Cross-platform file watching
- Debouncing pre batch uploads

### Nastavenia (settings.xml):
```xml
<category label="32001">  <!-- General -->
    <setting id="enabled" type="bool" label="32010" default="true"/>
    <setting id="cloud_provider" type="enum" label="32011" lvalues="32020|32021" default="0"/>
    <setting id="sync_interval" type="slider" label="32012" default="300" range="60,60,3600" option="int"/>
</category>

<category label="32002">  <!-- Authentication -->
    <setting id="gd_client_id" type="text" label="32030" default="" visible="eq(-2,0)"/>
    <setting id="gd_client_secret" type="text" label="32031" option="hidden" default="" visible="eq(-3,0)"/>
    <setting id="od_client_id" type="text" label="32032" default="" visible="eq(-4,1)"/>
</category>

<category label="32003">  <!-- Sync Options -->
    <setting id="sync_watched" type="bool" label="32040" default="true"/>
    <setting id="sync_resume_points" type="bool" label="32041" default="true"/>
    <setting id="sync_favorites" type="bool" label="32042" default="true"/>
    <setting id="sync_sources" type="bool" label="32043" default="false"/>
    <setting id="sync_playlists" type="bool" label="32044" default="false"/>
</category>
```

### Kľúčové features implementácie:

#### Real-time sync mechanism:
- Sledovanie `MyVideos` databázy cez JSON-RPC
- File system monitoring pre userdata súbory
- Event-driven architecture s queue systemom
- Debouncing pre zabránenie spam synchronizácie

#### Conflict resolution:
- **Last writer wins** (default)
- **Merge strategies** pre rôzne typy dát
- **User notification** pri konfliktoch
- **Backup system** pred konfliktným merge

#### Performance optimizations:
- **Incremental sync** - len zmeny od poslednej sync
- **Compression** pre veľké súbory
- **Batch operations** pre multiple files
- **Background threads** pre non-blocking operácie
- **Local caching** pre metadata

#### Error handling:
- **Retry mechanism** s exponential backoff
- **Network error handling**
- **API rate limiting** compliance
- **Graceful degradation** pri cloud outage
- **Detailed logging** pre debugging

## Implementation approach

### Fáza 1: Core service infrastructure
1. Vytvor základnú service architektúru
2. Implementuj settings system a logging
3. Vytvor base cloud provider interface

### Fáza 2: Database monitoring
1. JSON-RPC API integrácia pre Kodi database
2. Real-time detection watched status changes
3. Resume points tracking

### Fáza 3: File monitoring
1. Cross-platform file watching
2. Userdata súbory monitoring
3. Change detection a batching

### Fáza 4: Google Drive integration
1. OAuth2 authentication flow
2. Upload/download mechanisms
3. Conflict resolution

### Fáza 5: Synchronization engine
1. Bidirectional sync logic
2. Conflict resolution strategies
3. Performance optimizations

### Fáza 6: UI a user experience
1. Settings interface
2. Status notifications
3. Manual sync triggers

## Technické poznámky

### Kodi specifika:
- Použij `xbmc.Monitor` pre lifecycle management
- `xbmcaddon.Addon()` pre settings access
- `xbmc.translatePath()` pre userdata paths
- JSON-RPC cez `xbmc.executeJSONRPC()`
- Thread-safe logging cez `xbmc.log()`

### Cloud API considerations:
- **Google Drive API v3** s proper OAuth2 flow
- **Microsoft Graph API** pre OneDrive
- Token refresh handling
- Rate limiting compliance
- Error recovery mechanisms

### Cross-platform compatibility:
- Python 3.x compatibility (Kodi 19+)
- Path handling pre rôzne OS
- File permissions handling
- Network connectivity detection

### Security:
- Secure token storage
- No hardcoded credentials
- User consent pre cloud access
- Data encryption pre sensitive info

## Očakávané výstupy

1. **Kompletný addon** so všetkými súbormi
2. **Dokumentácia** pre inštaláciu a konfiguráciu
3. **Debug logging** pre troubleshooting
4. **Unit testy** pre core funkcionalitu
5. **Installation guide** pre end users

## Dodatočné požiadavky

- Code má byť dobre komentovaný a dokumentovaný
- Používaj type hints kde je to možné
- Implementuj proper exception handling
- Vytvor clear separation of concerns
- Addon má byť pripravený na publikovanie v Kodi repo

Začni s vytvorením základnej service architektúry a postupne pridávaj funkcionalitu. Potrebujem aby addon fungoval spoľahlivo a mal dobrú performance i pri veľkých databázach.