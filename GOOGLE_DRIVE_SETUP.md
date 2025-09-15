# Google Drive API Setup Instructions

## 🔧 Pre CloudSync Addon

### Krok 1: Vytvorenie Google Cloud Project

1. **Otvorte Google Cloud Console:**
   - Idite na: https://console.cloud.google.com/

2. **Vytvorte nový projekt:**
   - Kliknite "Select a project" → "New Project"
   - **Project name**: `CloudSync Kodi`
   - **Organization**: Nechajte prázdne (personal)
   - Kliknite **"Create"**

### Krok 2: Povolenie Google Drive API

1. **V ľavom menu:**
   - **APIs & Services** → **Library**

2. **Hľadajte "Google Drive API":**
   - Kliknite na **"Google Drive API"**
   - Kliknite **"Enable"**

### Krok 3: Vytvorenie OAuth 2.0 Credentials

1. **V ľavom menu:**
   - **APIs & Services** → **Credentials**

2. **Kliknite "+ Create Credentials":**
   - Vyberte **"OAuth client ID"**

3. **Ak sa zobrazí "Configure consent screen":**
   - Kliknite **"Configure consent screen"**
   - **User Type**: Vyberte **"External"**
   - Kliknite **"Create"**

4. **OAuth consent screen - Mandatory info:**
   - **App name**: `CloudSync for Kodi`
   - **User support email**: Váš email
   - **Developer contact information**: Váš email
   - Kliknite **"Save and Continue"**

5. **Scopes:** (Kliknite "Save and Continue" bez pridávania)

6. **Test users:** (Pridajte svoj Google email)
   - Kliknite **"+ Add users"**
   - Zadajte svoj Google email
   - Kliknite **"Save and Continue"**

7. **Summary:** Kliknite **"Back to Dashboard"**

### Krok 4: Vytvorenie OAuth Client ID

1. **Späť v Credentials:**
   - Kliknite **"+ Create Credentials"** → **"OAuth client ID"**

2. **Application type:**
   - Vyberte **"Desktop application"**
   - **Name**: `CloudSync Kodi Client`
   - Kliknite **"Create"**

3. **Uložte si credentials:**
   - **Client ID**: `xxx.apps.googleusercontent.com`
   - **Client Secret**: `GOCSPX-xxxxx`
   - Kliknite **"Download JSON"** (záloha)

### Krok 5: Konfigurácia v Kodi

1. **Otvorte Kodi CloudSync nastavenia:**
   - Settings → Add-ons → My add-ons → Services → CloudSync → Configure

2. **Google Drive tab:**
   - **Client ID**: Vložte Client ID z kroku 4
   - **Client Secret**: Vložte Client Secret z kroku 4

3. **Kliknite "Authenticate with Google Drive"**

### ⚠️ Dôležité poznámky:

- **App je v "Test mode"** - funguje len pre test users
- **Pre produkčné použitie** treba požiadať o verification (Google review)
- **Test users limit**: 100 používateľov
- **Refresh token**: Platí dokiaľ nevyprší (obvykle 1 týždeň bez aktivity v test mode)

### 🔍 Troubleshooting:

**Problem**: "redirect_uri_mismatch"
- **Riešenie**: Skontrolujte, že používate desktop application type

**Problem**: "access_denied"  
- **Riešenie**: Skontrolujte, že váš email je pridaný v test users

**Problem**: "invalid_client"
- **Riešenie**: Skontrolujte Client ID a Client Secret

### 📱 Pre Android Kodi:
- OAuth callback funguje cez localhost
- Môže byť potrebné povoliť "Unknown sources" v Android nastaveniach
- Niekto Android zariadenia blokujú localhost - použite iné zariadenie pre auth

---
*Tieto inštrukcie sú pre development/testing účely*