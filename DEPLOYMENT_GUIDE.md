# 🚀 CloudSync Deployment Guide

Complete guide for setting up automated releases and updates for CloudSync Kodi addon.

## 📋 Quick Setup Checklist

### 1. Create GitHub Repository
- [ ] Create public repo: `kodi-cloudsync`
- [ ] Add description: "CloudSync - Comprehensive Kodi addon for syncing across devices using Dropbox"
- [ ] Enable Issues and Discussions

### 2. Upload Project Files
```bash
# In your project directory
git init
git add .
git commit -m "Initial CloudSync v4.1.2 release"
git branch -M main
git remote add origin https://github.com/fifthy52/kodi-cloudsync.git
git push -u origin main
```

### 3. Update Repository URLs
Replace `YOUR_USERNAME` in these files:
- [ ] `README.md` - Update GitHub links
- [ ] `repository.cloudsync/addon.xml` - Update raw GitHub URLs
- [ ] `repository.cloudsync/addons.xml` - Update website/source URLs

### 4. Generate Repository Files
```bash
python generate_repository.py
```

### 5. Create First Release
```bash
git add .
git commit -m "Add repository structure and deployment files"
git push

# Create release tag
git tag v4.1.2
git push --tags
```

## 🔄 Automated Workflow

Once set up, future releases are automatic:

1. **Update addon version** in `service.cloudsync/addon.xml`
2. **Update repository** with `python generate_repository.py`
3. **Create release tag**: `git tag v4.1.3 && git push --tags`
4. **GitHub Actions automatically**:
   - Creates release on GitHub
   - Builds addon zip
   - Generates checksums
   - Updates download links

## 📦 Installation Methods for Users

### Method 1: Direct Install (Simple)
1. Go to [Releases](https://github.com/fifthy52/kodi-cloudsync/releases)
2. Download latest `service.cloudsync-x.x.x.zip`
3. Install via Kodi → Install from zip file

### Method 2: Repository Install (Auto-updates)
1. Download `repository.cloudsync.zip` from releases
2. Install repository in Kodi
3. Install CloudSync from repository
4. **Automatic updates!** 🎉

## 🛠️ Repository Structure

```
kodi-cloudsync/
├── .github/workflows/release.yml    # Automatic releases
├── service.cloudsync/               # Main addon
│   ├── addon.xml                   # Version info here
│   ├── service_v2.py
│   └── resources/
├── repository.cloudsync/            # Repository metadata
│   ├── addon.xml                   # Repository config
│   ├── addons.xml                  # Addon catalog
│   └── addons.xml.md5             # Generated checksum
├── generate_repository.py           # Repository builder
├── README.md                       # GitHub homepage
└── DEPLOYMENT_GUIDE.md            # This file
```

## 🔄 Release Process

### For New Versions:

1. **Develop & Test** addon changes
2. **Update version** in `service.cloudsync/addon.xml`
3. **Update changelog** in `repository.cloudsync/addons.xml`
4. **Generate repository**: `python generate_repository.py`
5. **Commit changes**: `git add . && git commit -m "Release v4.1.3"`
6. **Create tag**: `git tag v4.1.3`
7. **Push**: `git push && git push --tags`
8. **GitHub Actions** handles the rest!

## ✅ Benefits

- **No more manual zip uploads** to devices
- **Automatic updates** for users with repository
- **Professional release management**
- **Version tracking** and checksums
- **Easy rollback** to previous versions
- **GitHub Issues** for user support
- **Professional presentation** on GitHub

## 🎯 User Experience

**Before:** Manual zip download → USB transfer → Manual install
**After:** Install repository once → Automatic updates forever!

Your users will love the professional experience! 🚀