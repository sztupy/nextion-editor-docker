# NSPanel Blueprint Background Generator

This add-on allows you to generate custom TFT files for your NSPanel when using NSPanel Blueprint.

> **Note:** This addon currently only supports `amd64` as a platform, for example a Home Assistant setup installed on an Intel NUC. This will not yet work on any ARM based computers, for example on Raspberry Pi based installs, nor on Home Assitant Green!

> **Note:** This addon requires around 2-3 GB of disk space to install

## Setup

1. When generating your ESPHome config for your NSPanel, make sure you set a custom nextion url. For example:
 
   ```
   substitutions:
     nextion_update_url: "http://homeassistant.local:8123/local/nspanel_living_room.tft"
   ```
   
   If you have multiple devices, make sure each uses a separate link.

2. Rebuild your ESPHome settings and install the updated settings to your NSPanel

3. Upload a background image
 
   This should be uploaded somewhere to your Home Assistant `/config` folder, for example `/config/nspanel-generator/living_room.png`. You can use various tools, like the [SSH Addon](https://community.home-assistant.io/t/home-assistant-community-add-on-ssh-web-terminal/33820) or the [Visual Studio Code Addon](https://community.home-assistant.io/t/home-assistant-community-add-on-visual-studio-code/107863) to do this.
   
   > **Note:** Make sure the image is `480x320` in resolution for landscape NSPanels (EU, US Landscape), and `320x480` for portrait (US default) versions. The file extensions needs to be `png`, and it should not be transparent.

4. Install this addon. Open up the configuration and set it up the following way:
   
   ```yaml
   main: "living-room"
   configs:
     - name: living-room
       result: nspanel_living_room.tft
       base: eu
       background: /nspanel-generator/living_room.png    
   ```
   
   Config documentation:
   * `name`: Custom name for your config. Make sure it is unique. Prefer only using lowercase letters, and dashes
   * `result`: The name of the file to generate. This will be accessible at `http://homeassistant.local:8123/local/<name>`. This should match the setting set up at point 1 above
   * `base`: The type of NSPanel to install. Available options are: `eu`, `us`, `usland`, `eucjk`, `uscjk`, `uslandcjk`.
   * `background`: The background image to use. Make sure this is put in the `/config` folder for your Home Assistant install, se point 3 above.
   
   You can have multiple configs set up, but the app will only generate one TFT file at a time. You can point your `main` value to another config, and re-run the Add On if you need to generate the TFT file for multiple configs.

5. Run the addon. Wait for it to finish, as it might take a while.
   
   A successful run will have logs like this:
   
   ```
   + ./update_images.sh
   Waiting for application to boot
   Waiting for object AutomationID=pp2 AND Name=OK ...
   Waiting for object AutomationID=pp2 AND Name=OK ...
   Waiting for object AutomationID=pp2 AND Name=OK ...
   Waiting for object AutomationID=pp2 AND Name=OK ...
   Error during enumeration  retrying...
   Waiting for object AutomationID=pp2 AND Name=OK ...
   Started processing
   Waiting for Page Panels to load 
   Waiting for element: Page Panels 
   Waiting for object AutomationId=colListBox1 AND IsEnabled=1 ...
   Clicking at location 
   Deleting old images 
   Waiting for object AutomationId=picListBox0 AND IsEnabled=1 ...
   Confirm to delete 
   Waiting for object AutomationID=pp1 AND Name=Yes ...
   Add images 
   Import dialog 
   Waiting for object LocalizedControlType=dialog AND Name=Open ...
   Waiting for import 
   Waiting for object AutomationID=pp2 AND Name=OK ...
   Waiting for object AutomationID=pp2 AND Name=OK ...
   Save file 
   Waiting for object AutomationId=buttonX2 AND Name=Output ...
   Wait for save to finish 
   Waiting for object AutomationId=buttonX2 to disappear...
   Waiting for object AutomationId=buttonX2 to disappear...
   + sudo mkdir -p /haconfig/www
   + sudo cp input/output.tft /haconfig/www/nspanel_living_room.tft
   + sudo cp input/output.hmi /haconfig/www/nspanel_living_room.tft.hmi
   ```
   
   If however you get an error like at any point:
   
   ```
   Could not find element AutomationID=pp1 AND Name=Yes Exiting
   ```
   
   then you should restart the add-on, so it can retry.
   
   If it still doesn't work after 2-3 retries, and always hangs at the same place, then [please create a bugreport](https://github.com/sztupy/nextion-editor-docker/issues) with the contents of your log and the type of machine you have.

6. If it did generate the file, then go to Settings -> Devices -> ESPHome, and select the NSPanel device.
   
   Once opened change the "Update TFT Display - Model" setting to "Use nextion_update_url", then finally click the "Press" button on "Update TFT Display"
   
   ![Screenshot of the ESPHome settings you need to make](https://raw.githubusercontent.com/sztupy/nextion-editor-docker/refs/heads/main/hassio-nspanel-blueprint-generator/esphome-update.png)

7. Wait for the Upload to finish. If all goes well your panel will now use the updated background.