# Dropbox Setup - JEDNODUCHO! 🚀

## 📱 Len 3 kroky:

### Krok 1: Vytvorte Dropbox App
1. Idite na: **https://www.dropbox.com/developers/apps**
2. Kliknite **"Create app"**
3. Vyberte:
   - **Scoped access** ✅
   - **Full Dropbox** ✅  
   - **Name your app**: `KodiSync-YourName` (musí byť unique)
4. Kliknite **"Create app"**

### Krok 2: Získajte Access Token
1. V novej app na stránke **"Settings"** tab
2. Scroll down na **"Generated access token"**
3. Kliknite **"Generate"** 
4. **Skopírujte token** (začína `sl.` alebo `slr.`)

⚠️ **Token je tajný! Nikomu ho neukazujte!**

### Krok 3: Vložte do Kodi
1. **Kodi → Settings → Add-ons → CloudSync → Configure**
2. **Dropbox tab:**
   - **Access Token**: Vložte token z kroku 2
   - **Sync Folder**: `/KodiSync` (alebo zmeňte)
3. Kliknite **"Test Connection"**
4. Mal by zobraziť **"Connection Successful!"**

## ✅ Hotovo! 

Addon teraz môže:
- ✅ Čítať/písať do vašej Dropbox
- ✅ Vytvoriť sync folder automaticky
- ✅ Synchronizovať dáta medzi zariadeniami

## 🔧 Nastavenia:

**Sync Options tab:**
- ☑️ Sync Watched Status (sledované filmy/seriály)
- ☑️ Sync Resume Points (pozície prehrávania) 
- ☑️ Sync Favorites (obľúbené)
- ☐ Sync Sources (zdroje médií)
- ☐ Sync Playlists (playlisty)

## 🆘 Problémy?

**"Invalid access token"**
- ✅ Skontrolujte, že token je správne skopírovaný
- ✅ Token začína `sl.` alebo `slr.`
- ✅ Token je z **"Generated access token"** sekcie

**"Connection failed"**
- ✅ Skontrolujte internet pripojenie
- ✅ Firewall neblokuje Kodi

**"Folder creation failed"**  
- ✅ App má **"Full Dropbox"** permissions
- ✅ Skúste zmeniť sync folder názov

## 🎯 Vs. Google Drive:
- **Dropbox**: 1 token → hotovo ✅
- **Google Drive**: OAuth2, consent screen, 10+ krokov ❌

**Dropbox wins!** 🏆

---
*Jednoduchosť je krásna* ✨