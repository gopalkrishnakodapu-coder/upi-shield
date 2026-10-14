# Deploy UPI Shield and install it as an app

## Step 1: Put the project on GitHub
1. Create a free account at github.com and click New repository (name: upi-shield, Public).
2. Unzip this project. On the repository page click "uploading an existing file", drag in ALL files and folders, then Commit.

## Step 2: Deploy on Render (free)
1. Go to render.com, sign up with GitHub.
2. New + > Blueprint > pick your repository > Apply. (render.yaml is already set up.)
3. Wait 3-6 minutes. You get a link like https://upi-shield-xxxx.onrender.com
4. Open https://YOUR-LINK/pay.html on your phone. Dashboard is https://YOUR-LINK/

## Step 3A: Install on a phone (fastest, no APK needed)
- Android (Chrome): open the pay link > tap "Install app" at the top, or menu (3 dots) > Install app / Add to Home screen.
- iPhone (Safari): Share button > Add to Home Screen.
It opens full screen with its own icon, like a normal app.

## Step 3B: Make a real APK (like your friend's) with PWABuilder
1. Open pwabuilder.com and paste https://YOUR-LINK/pay.html
2. Click Start, then Package for stores > Android > Generate.
3. Download the zip, unzip, install the "signed .apk" on your phone (allow "install unknown apps").

## Notes
- Free Render sleeps after ~15 min idle (first open takes ~1 minute) and forgets accounts when it restarts. For permanent accounts use a paid plan with a Disk, or an external database.
- Camera/screenshot scanning and opening GPay/PhonePe/Paytm need the HTTPS link (Render provides it).
