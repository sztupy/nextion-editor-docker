# NSPanel Easy Background Generator

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fsztupy%2Fnextion-editor-docker)

This add-on allows you to generate custom TFT files for your NSPanel when using [NSPanel Easy](https://github.com/edwardtfn/NSPanel-Easy), mainly by allowing replacing the background images:

<div align="center">
  <img title="Example screenshot with library background" src="https://raw.githubusercontent.com/sztupy/nextion-editor-docker/refs/heads/main/images/example_library.jpg" width="270"/>
  <img title="Example screenshot with bedroom background" src="https://raw.githubusercontent.com/sztupy/nextion-editor-docker/refs/heads/main/images/example_bedroom.jpg" width="270"/>
</div>

> **Note:** This addon currently only supports `amd64` as a platform, for example a Home Assistant setup installed on an Intel NUC. This will not work on any ARM based computers, for example on Raspberry Pi based installs, nor on Home Assitant Green!

> **Note:** This addon requires around 2-3 GB of disk space to install, and at least 4GB of RAM to function properly, but 8GB is highly recommended.

## Setup

1. Upload a background image

   This should be uploaded somewhere to your Home Assistant `/config` folder, for example `/config/nspanel-generator/living_room.png`. You can use various tools, like the [SSH Addon](https://community.home-assistant.io/t/home-assistant-community-add-on-ssh-web-terminal/33820) or the [Visual Studio Code Addon](https://community.home-assistant.io/t/home-assistant-community-add-on-visual-studio-code/107863) to do this.

   > **Note:** Make sure the image is `480x320` in resolution for landscape NSPanels (EU and US Landscape), and `320x480` for portrait (US) versions. The file extensions needs to be `png`, and it should not be transparent.

   > **Note:** You can find a few examples for EU/landscape orientation [here](https://github.com/sztupy/nextion-editor-docker/tree/main/images/backgrounds)

2. Install this addon. Open up the configuration and set it up the following way:

   ```yaml
   main: "living-room"
   configs:
     - name: living-room
       result: nspanel_living_room
       base: portrait
       background:
         dark: nspanel-generator/living_room.png
         light: nspanel-generator/living_room.png
         splash: nspanel-generator/living_room.png
   ```

   Config documentation:
   * `name`: Custom name for your config. Make sure it is unique. Prefer only using lowercase letters, and dashes
   * `result`: The name of the file to generate. This will be accessible at `http://homeassistant.local:8123/local/<name>`. This needs to match the setting you will set up at point 4 later in this guide.
   * `base`: The type of NSPanel TFT to generate. Available options are: `portrait` for EU, and `landscape` for US devices.
   * `background`: The background images to use. Make sure these images are put in the `/config` folder for your Home Assistant install, se point #1 above. You don't need to provide all three images in which case the default background will be kept.

   You can have multiple configurations set up, but the app will only generate one TFT file at a time. You can point your `main` value to the `name` value of another config, and re-run the Add On, to generate the TFT file for that particular config.

3. Run the addon. Wait for it to finish, as it might take a while.

   A successful run will have logs like this:

   ```
   + ./update_images.sh png 95
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
   + sudo mkdir -p /haconfig/www/nspanel_living_room
   + sudo cp input/output.tft /haconfig/www/nspanel_living_room/nspanel_landscape.tft
   + sudo cp input/output.hmi /haconfig/www/nspanel_living_room/nspanel_landscape.hmi
   ```

   If however you get an error like at any point:

   ```
   Could not find element AutomationID=pp1 AND Name=Yes Exiting
   ```

   then you should restart the add-on, so it can retry.

   If it still doesn't work after a few retries, especially if it always hangs at the same place, then [please create a bugreport](https://github.com/sztupy/nextion-editor-docker/issues) with the contents of your log and the type of machine you have.

4. Update your ESPHome config for your NSPanel, and make sure you set the location to the `<result>` value you set up earlier. For example:

   ```
   substitutions:
     nextion_update_url: "http://homeassistant.local:8123/local/nspanel_living_room"
   ```

   If you have multiple devices with different backgrounds, make sure each uses a separate `result` link.

   NSPanel Easy will then download the file from `http://homeassistant.local:8123/local/nspanel_living_room/nspanel_landscape.tft` (or `portrait` for US devices)

5. Rebuild your ESPHome settings and install the updated settings to your NSPanel

6. If all is well then go to Settings -> Devices -> ESPHome, and select the NSPanel device.

   Once opened click the "Press" button on "Update TFT Display"

7. Wait for the Upload to finish. If all goes well your panel will now use the updated background.

8. If you update your NSPanel Easy, make sure to re-build your TFT files one-by-one. The app will always download the latest NSPanel Easy version for building
