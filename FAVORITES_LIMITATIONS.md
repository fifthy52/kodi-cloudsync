# 🚨 Favorites Synchronization Limitations

## The Problem

Kodi has **no reliable built-in method** to refresh the favorites display when `favourites.xml` is modified externally by add-ons.

## Technical Details

According to official Kodi documentation:
- No built-in function exists to reload `favourites.xml`
- Changes to the file are not automatically reflected in the GUI
- The only known workaround is `LoadProfile()` but this causes significant UX issues

## Arctic Zephyr Skin Specifics

Arctic Zephyr loads favorites via `MyFavourites.xml` and may cache the data differently than other skins, making refresh even more challenging.

## CloudSync's Approach

### Current Implementation
- **Experimental setting**: "Try Favorites Refresh (Experimental)" (disabled by default)
- Uses `ReloadSkin()` builtin - may not work for all skins
- Only attempts refresh if user explicitly enables it

### Why It's Optional
1. **Effectiveness varies by skin** - Arctic Zephyr may not respond
2. **UX impact** - Skin reload causes brief flash/interruption
3. **Alternative exists** - Manual Kodi restart always works

## Recommendations for Users

### If Favorites Don't Update After Sync:
1. **Restart Kodi** (most reliable)
2. Try enabling "Favorites Refresh" setting (experimental)
3. Use different skin that handles favorites refresh better

### Alternative Workflow:
- Sync favorites on one "master" device
- Other devices: restart Kodi after initial sync to see favorites
- Subsequent changes sync in background, restart when convenient

## For Developers

This is a **known Kodi limitation**, not a CloudSync bug. Other sync add-ons face the same issue.

The only "guaranteed" methods have severe UX drawbacks:
- `LoadProfile(Master user)` - causes profile switch animation
- Full Kodi restart - interrupts media playback

## Status

- ✅ Favorites sync perfectly (file level)
- ⚠️ Display refresh unreliable (Kodi limitation)
- 🔄 Setting provided for users to experiment
- 📖 Documented for transparency