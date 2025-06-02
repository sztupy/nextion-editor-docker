Nextion Editor Docker
=====================

Nextion Editor running under Wine 10.0 & Docker to allow Nextion TFT files to be built in a more automated way. Also includes AutoHotKey with UIAutomation support to allow Nextion's GUI to be controlled from scripts.

Docker hub link: https://hub.docker.com/r/sztupy/nextion-editor

![Example image of Nextion Editor displaying NSPanel Blueprint](images/example.png)

## Build

To build the docker container locally do the following:

```sh
docker/build.sh
```

This will download the following files:

* Nextion Editor
* Windows KB971513 Patch (required to support UIAutomation under Wine 10.0)
* AutoHotKey 1.1
* Pulovers Macro Editor (specifically a bloatware-removed version)
* UIAViewer for AHK

And then build a docker-wine container with the required apps pre-installed at

* `C:\data` (Windows path)
* `/home/wineuser/.wine/drive_c/data` (Linux path)

## Run graphical mode

After the container has been built you can start up Wine in RDP mode using

```sh
docker run -it --rm \
  -v ${PWD}:/app/input \
  --hostname="nextion-editor" \
  --env="RDP_SERVER=yes" \
  --publish="3389:3389/tcp" \
  sztupy/nextion-editor:latest
```

Once started you can connect to this container via Remote Desktop on `localhost:3389`. Username and password is `wineuser`. Nextion Editor will be available on the Desktop. Files will be available at `Z:\app\input` however please note you will need to copy them over to ``C:\`` for Nextion to be able to access them.

You can also use UIAutomation Viewer to plan your macro if you want to automate what you're doing.

## Run command line mode

The container includes AHK and UIAutomation to automate some common tasks without needing a GUI or any manual intervention. Most scripts will start up Nextion, click around the GUI to do their work, and finally put the resulting files under `/app` so they can then be downloaded from the container. While the scripts generally try to be clever, this is not always possible and might resort to mouse clicks on specific locatons on the screen. Generally all scripts expect Nextion to run under a resolution of 1024x768.

### Compile / Build TFT files from HMI

The following script will load up a HMI file, then compile and save it as a TFT file.

Name your file `input.hmi`

```sh
docker run -it --rm \
  -v ${PWD}:/app/input \
  sztupy/nextion-scripts:latest \
  ./compile.sh
```

Outputs will be `output.hmi` and `output.tft`

### Update the version number in an NSPanel Blueprint HMI file

Name your file `input.hmi`

```sh
docker run -it --rm \
  -v ${PWD}:/app/input \
  sztupy/nextion-scripts:latest \
  ./update_version.sh <VERSION_NUMBER>
```

Outputs will be `output.hmi` and `output.tft`

### Batch updating images in a HMI file

The following script will load up a HMI file, remove all images from it, then re-import them from a directory. Once updated it will save the HMI file and compile it as well to TFT

Name your file `input.hmi`. Put images you wish to upload to a folder named `pics`

```sh
docker run -it --rm \
  -v ${PWD}:/app/input \
  sztupy/nextion-scripts:latest \
  ./update_images.sh
```

Outputs will be `output.hmi` and `output.tft`

### Debugging scripts

To debug any of the scripts you can do:

```sh
docker run -it --rm \
  -v ${PWD}:/app/input \
  sztupy/nextion-scripts:latest \
  bash
```

then in the shell run:

```sh
./dump_screenshots.sh &
./<original_command.sh>
```

This will create screenshots of what's happening on the screen in your local folder that you can check later.
