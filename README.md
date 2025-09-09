# Docker Wyze Bridge (redux)

[![Docker](https://github.com/waelsamy/docker-wyze-bridge/actions/workflows/docker-image.yml/badge.svg)](https://github.com/waelsamy/docker-wyze-bridge/actions/workflows/docker-image.yml)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/waelsamy/docker-wyze-bridge?logo=github)](https://github.com/waelsamy/docker-wyze-bridge/releases/latest)
[![Docker Image Size (latest semver)](https://img.shields.io/docker/image-size/waelewida/wyze-bridge?sort=semver&logo=docker&logoColor=white)](https://hub.docker.com/r/waelewida/wyze-bridge)
[![Docker Pulls](https://img.shields.io/docker/pulls/waelewida/wyze-bridge?logo=docker&logoColor=white)](https://hub.docker.com/r/waelewida/wyze-bridge)

## WebRTC/RTSP/RTMP/HLS Bridge for Wyze Cam

![479shots_so](https://user-images.githubusercontent.com/67088095/224595527-05242f98-c4ab-4295-b9f5-07051ced1008.png)

Create a local WebRTC, RTSP, RTMP, or HLS/Low-Latency HLS stream for most of your Wyze cameras including the outdoor, doorbell, and 2K cams.

No modifications, third-party, or special firmware required.

It just works!

Streams direct from camera without additional bandwidth or subscriptions.

Please consider ⭐️ starring or [☕️ sponsoring](https://ko-fi.com/mrlt8) this project if you found it useful, or use the [affiliate link](https://amzn.to/3NLnbvt) when shopping on amazon!

> [!IMPORTANT]
> As of May 2024, you will need an API Key and API ID from: [Wyze Support Article](https://support.wyze.com/hc/en-us/articles/16129834216731).
>
> [!WARNING]
> Please double check your router/firewall and do NOT forward ports or enable DMZ access to the bridge unless you know what you are doing!

![Wyze Cam V1](https://img.shields.io/badge/wyze_v1-yes-success.svg)
![Wyze Cam V2](https://img.shields.io/badge/wyze_v2-yes-success.svg)
![Wyze Cam V3](https://img.shields.io/badge/wyze_v3-yes-success.svg)
![Wyze Cam V3 Pro](https://img.shields.io/badge/wyze_v3_pro-yes-success.svg)
![Wyze Cam V4](https://img.shields.io/badge/wyze_v4-yes-success.svg)
![Wyze Cam Floodlight](https://img.shields.io/badge/wyze_floodlight-yes-success.svg)
![Wyze Cam Floodlight V2](https://img.shields.io/badge/wyze_floodlight_v2-yes-success.svg)
![Wyze Cam Pan](https://img.shields.io/badge/wyze_pan-yes-success.svg)
![Wyze Cam Pan V2](https://img.shields.io/badge/wyze_pan_v2-yes-success.svg)
![Wyze Cam Pan V3](https://img.shields.io/badge/wyze_pan_v3-yes-success.svg)
![Wyze Cam Pan Pro](https://img.shields.io/badge/wyze_pan_pro-yes-success.svg)
![Wyze Cam Outdoor](https://img.shields.io/badge/wyze_outdoor-yes-success.svg)
![Wyze Cam Outdoor V2](https://img.shields.io/badge/wyze_outdoor_v2-yes-success.svg)
![Wyze Cam Doorbell](https://img.shields.io/badge/wyze_doorbell-yes-success.svg)
![Wyze Cam Doorbell V2](https://img.shields.io/badge/wyze_doorbell_v2-yes-success.svg)

See the [supported cameras](#supported-cameras) section for additional information.

## Quick Start

Install [docker](https://docs.docker.com/get-docker/) and run:

```bash
docker run -p 8554:8554 -p 8888:8888 -p 5050:5000 -e WB_AUTH=false waelewida/wyze-bridge
```

You can then use the web interface at `http://localhost:5050` where `localhost` is the hostname or ip of the machine running the bridge.

See [basic usage](#basic-usage) for additional information or visit the [wiki page](https://github.com/waelsamy/docker-wyze-bridge/wiki/Home-Assistant) for additional information on using the bridge as a Home Assistant Add-on.

## What's Changed in v3.12.3

Cleaned up the threading logic around startup/shutdown to reduce CPU and memory leaks

- Added validation checks for the API Key ID and API Key to help prevent issues logging in Fixes #47
- Cleaned up the thread and process tracking to ensure that we release threads when they're done
- Only allow one running purge thread per camera Fixes #40
- Added timeouts to all the thread `.join()`s to ensure we don't hang waiting for threads to die off
- Increased the buffer site for the pipe reads to reduce CPU load
- Consistently swallow ValueError, AttributeError, RuntimeError, and FileNotFound errors so sub-processes and threads terminate correctly

Note: v3.12.2 was everything above, but missing the change notes, oops.

## What's Changed in v3.12.1

Cleaned MQTT logic and pull in some others' changes

### New features

Automatic Sunrise/Sunset snapshots drive ny the `LONGITUDE` and `LATITUDE` configuration variables.
`FORCE_IOTC_DETAIL` if true will force detailed debugging for the IOTC subsystem which can be used to decode a camera's protocol messages.

- MQTT cleanup with more logging and move configuration to config.py
- Read the TUTK device_config.json once not every interaction
- Gathering up other changes
  - Add GW_DBD Doorbell Duo to list not yet validated from @Angel-Vazquez change
  - Add SNAPSHOT_CAMERAS and  sunset/sunrise snapshots from @ruddell [see](https://github.com/mrlt8/docker-wyze-bridge/compare/main...ruddell:docker-wyze-bridge:sunrise-snapshotter
)
  - Picking up the relevant changes from p2pcam
- Cleanup of config circular dependencies
- Fix run if syntax old habits die hard

## What's Changed in v3.12.0

Cleaned up the startup logic to ensure things start quickly and moved configurations around so everything is overrideable

- Moved API-driven snapshots into the `Stream_Manager.py` so they don't delay startup.
- Clean up the /var/log directory in Dockerfile build image
- Better to supply empty, not samples in config
- Switch to `run` for diagnostic dump
- Deprecate the `config.yml` setting of environment variables so we can set the `IMG_DIR` and `RECORD_PATH` reliably even
  if not running inside Home Assistant as an add-on
- Remove the MTX_* variables from the `.env` as we want them to be settable in the options.
- Explicitly default the MTX settings that used to be forced (MTX_READTIMEOUT=30s, MTX_HLSVARIANT=mpegts, MTX_WRITEQUEUESIZE=2048) 
  to ensure backward compatibility
- Updated the defaults for the `IMG_DIR` and `RECORD_PATH` to match what the `.env` would have 
  previously set, but now it's overridable.
- Reduced log spam by making some `.info(` calls `.debug(`
- Don't emit ffmpeg non-error messages  (let the Popen eat them).

## What's Changed in v3.11.1

Turns out you cannot have a completely optional section in a config.yml

Use something like

```yaml
CAM_OPTIONS:
  - CAM_NAME: fake-camera-name
    RECORD: false
```

## What's Changed in v3.11.0

Cleanup of authorization logic and adding background activity

- RECORD **is working again**!
- Marked CAM_OPTIONS and MEDIAMTX as optional in the config
- Cleanup the snapshot pruning to ignore files going missing and
  use only prune each camera's path, not the entire image directory
- Added background pruning of snapshots to speed startup
- Fix forced DEBUG log level
- Fix LOW_LATENCY should be LLHLS
- Extend session connection timeout to 60 seconds
- Fixed FPS calculation
- Split out WyzeStreamOptions
- Split out StreamManager
- Make Stream know type of camera and options.
- Make WyzeStream be a Stream
- Reduced default logging level for ffmpeg
- Tons of logging cleanup
- Cleaned up warnings
  
## What's Changed in v3.10.14

- Made MQTT config value optional Fixes #39
- Fix MQTT parameters minimum value for bitrate and fps
- Don't emit MQTT state messages unless the state has changed
- Fix warning in  BOA check
- Add missing OFFLINE_TIME and DOMAIN options
- Added documentation of the option defaults.

## What's Changed in v3.10.13

- Fix schema for MQTT discovery messages

## What's Changed in v3.10.12

- Filled out the missing translations and docs
- Fix busted device configuration table (the device.json file had some XML in it)
- Fix bad handling of WYZEDB3 message protocol support
- Clean up wyzecam to adopt original upstream MAIN fixes
- Sync with upstream wysecam DEV branch
- Fix sleep when no data is ready (was waiting 0 seconds instead of the intended 1/80th of a second)
- Yield frame_info in the receive data iterations.
- Decode both FrameInfoStruct OR FrameInfo3Struct and whine if something is wrong.
- Don't discard messages without an expected_response_code as we know what it's supposed to be anyway.
- Proper type, use literals, better logging, eliminate dead code
- Remove exit logging
- Revert type of resend and remove redundant SDK license set
- Add resp so debug structure are visible

## What's Changed in v3.10.11

- Fix errors in startup avClientStartEx doesn't return a tuple
- Fix path construction for MediaMTX
- Fix python lint warnings and a whole lot of logging and type cleanup
- Move environment stuff to config and config reading out of mtx_server
- Don't complain about directories existing in migration
- Attempt to ensure directories for recordings
- Capture stdout of MediaMTX and openssl for logging
- Capture the traceback before context corrupted
- Switched to better logging syntax
- Let's declare the ports we EXPOSE in the Dockerfile(s)

## What's Changed in v3.10.10

- Add camera IP to MQTT message
- Adjust the recording path construction more
- Added STUN_SERVER support
- Switched all home assistant configs to host_network
- Don't default WB_AUTH nor MQTT on and don't force the MQTT_TOPIC
- Restored the fps to the K10056SetResolvingBit message
- Lots more logging to help track down the recording issue
- Cleanup a bunch of Python warnings
- Bump MediaMTX to 1.12.3
- Bump Wyze app version to 3.5.5.8
- Don't force MediaMTX logging level to info
- Better tagging for Docker images
- Unified more the normal/hardware/multiarch docker build files
- Add devcontainer.json and tasks.json for VSCode

## What's Changed in v3.10.9

- Revert tutk_protocol change in `K10056SetResolvingBit`

## What's Changed in v3.10.8

- Removed forced leading "/" from RECORD_PATH
- Removed the IP restrictions from the MediaMTX "publisher" role
- Sync up with Elliot Kroo's [wyzecam library](https://github.com/kroo/wyzecam)
  - add HL_WCO2 camera support
  - K10020CheckCameraParams support
  - Fix `authentication_type`'s type
  - Add fps to the `K10056SetResolvingBit` message
  - Fix time setting to always advance one second (for lag) in `K10092SetCameraTime`
  - Send/recv time and blank (PST flag?) to `K11006GetCurCruisePoint`/`K11010GetCruisePoints`/`K11012SetCruisePoints`
- Changed the MediaMTX config builder to emit correct config for recording
- Cleanup the warnings in the app code and added `mtx_event` pipe receipt logging
- Updated Wyze iOS app version to 3.5.0.8 (for user agent)
- Use `SIGTERM` for more graceful shutdown
- More startup logging for the MTX configuration of `RECORD_PATH`
- Sync up all the ports listed in MediaMTX with the ports exposed in the docker-compose files

## What's Changed in v3.10.7

- Reverted defaulting of RECORD_PATH option specifying `{cam_name}` instead of `%path` (need to fix that another way)
- Changed the MediaMTX config builder to emit correct config for recording.
  
## What's Changed in v3.10.6

- ~Changed the documentation and defaults for the RECORD_PATH option to specify `{cam_name}` instead of `%path` to
  eliminate recording errors~ Reverted in v3.10.7
- Add exception handling to ffmpeg pruning logic to prevent snapshot prunes from killing each other
- Now gathers the list of parents that might be pruned and does that after purging the files
- Fixed python lint message in get_livestream_cmd

## What's Changed in v3.10.5

- Fix regression for snapshot pruning

## What's Changed in v3.10.4

- Catch exceptions when pruning snapshots so we don't stop grabbing them if something breaks a prune.
- Allow the ffmpeg error messages to reach the normal runtime
- Bump to [MediaMTX 1.12.2](https://github.com/bluenviron/mediamtx/releases/tag/v1.12.2) to [fix regression on RaspberryPIs](https://github.com/bluenviron/mediamtx/compare/v1.12.1...v1.12.2)

## What's Changed in v3.10.3

- Bump MediaMTX to 1.12.1

## What's Changed in v3.10.2

- Added code to protect against the aggressive syntax check in MediaMTX 1.12.0 which
  complains about the `recordPath` missing required elements even when recording is
  not enabled (it really shouldn't validate that setting unless one or more paths
  request recording...and didn't through 1.11.3).
  For reference, the pattern is computed from our `RECORD_PATH` and `RECORD_FILE_NAME`
  settings and the combination of them must contain the `strftime` format specifiers
  of *either* a `"%s"` or **all** of of "%Y", "%m", "%d", "%H", "%M", "%S" (case-sensitive).
  If the value is not compliant, to keep MediaMTX from erroring out, we append `"_%s"` whatever
  was specified and emit a warning.
- Changed the default `RECORD_PATH` to ~`"record/%path/%Y/%m/%d/"`~ *v3.10.7* `"%path/{cam_name}/%Y/%m/%d"`
- Changed the default `RECORD_FILE_NAME` to `"%Y-%m-%d-%H-%M-%S"`

## What's Changed in v3.10.1

- Add `TOTP_KEY` and `MQTT_DTOPIC` to *config.yml* schema to avoid logged warning noise
- Add `MQTT_DTOPIC` to *config.yml* options to ensure a usable default
- Add `video: true` to all the *config.yml* variants to ensure hardware encoding can
  use video card
- Upgrade to `python:3.13-slim-bookworm` for docker base image
- Cleaned up Dockerfile scripts for testing and multiarch
- Safer docker build by testing the tarballs downloaded for MediaMTX or FFMpeg

## What's Changed in v3.10.0

- Attempt upgrade of MediaMTX to 1.12.0 (again)
- Fixed schema of RECORD_LENGTH config option (it needs an `s` or `h` suffix, so must be string)
- Added RECORD_KEEP to the config.yml so it can be actually be configured in the add-on

## What's Changed in v3.0.7

- Better logging of exceptions and pass the MediaMTX messages through to main logs
- Correct building of permissions for MediaMTX
- Documented all the possible points in the docker-compose files.

## What's Changed in v3.0.6

- Revert MediaMTX to 1.11.3 because 1.12 doesn't work here.

## What's Changed in v3.0.5 ~DELETED~

- Fix MediaMTX to pass a user name [since 1.12.0 now requires one](https://github.com/bluenviron/mediamtx/compare/v1.11.3...v1.12.0#diff-b5c575fc54691bae05c5cc598fac91c97876b3d15687c359f970a8b832ab3ab6R23-R41)

## What's Changed in v3.0.4  ~DELETED~

- Chore: Bump [MediaMTX to 1.12.0](https://github.com/bluenviron/mediamtx/releases/tag/v1.12.0)

## What's Changed in v3.0.3

Rehoming this to ensure it lives on since PR merges have stalled in the original (and most excellent) @mrlt8 repo, I am surfacing a new
release with the PRs I know work. **Note** The badges on the GitHub repo may be broken and the donation links *still* go to @mrlt8 (as they should!)

- Chore: Bump Flask to 3.1.*
- Chore: Bump Pydantic to 2.11.*
- Chore: Bump Python-dotenv to 1.1.*
- Chore: Bump MediaMTX to 1.11.3
- FIX: Add host_network: true for use in Home Assistant by @jdeath to allow communications in Docker
- FIX: Hardware accelerated rotation by @giorgi1324
- Enhancement: Add more details to the cams.m3u8 endpoint by @IDisposable
- FIX: Fix mixed case when URI_MAC=true by @unlifelike
- Update: Update Homebridge-Camera-FFMpeg documentation link by @donavanbecker
- FIX: Add formatting of {cam_name} and {img} to webhooks.py by @traviswparker which was lost
- Chore: Adjust everything for move to my GitHub repo and Docker Hub account

## What's Changed in v2.10.3

- FIX: Increased `MTX_WRITEQUEUESIZE` to prevent issues with higher bitrates.
- FIX: Restart RTMP livestream on fail (#1333)
- FIX: Restore user data on bridge restart (#1334)
- NEW: `SNAPSHOT_KEEP` Option to delete old snapshots when saving snapshots with a timelapse-like custom format with `SNAPSHOT_FORMAT`. (#1330)
  - Example for 3 min: `SNAPSHOT_KEEP=180`, `SNAPSHOT_KEEP=180s`, `SNAPSHOT_KEEP=3m`
  - Example for 3 days: `SNAPSHOT_KEEP=72h`, `SNAPSHOT_KEEP=3d`
  - Example for 3 weeks: `SNAPSHOT_KEEP=21d`, `SNAPSHOT_KEEP=3w`
- NEW: `RESTREAMIO` option for livestreaming via [restream.io](https://restream.io). (#1333)
  - Example `RESTREAMIO_FRONT_DOOR=re_My_Custom_Key123`

## What's Changed in v2.10.2

- FIX: day/night FPS slowdown for V4 cameras (#1287) Thanks @cdoolin and @Answer-1!
- NEW: Update battery level in WebUI

## What's Changed in v2.10.0/v2.10.1

FIXED: Could not disable `WB_AUTH` if `WB_API` is set. (#1304)

### WebUI Authentication

Simplify default credentials for the WebUI:

- This will not affect users who are setting their own `WB_PASSWORD` and `WB_API`.
- Default `WB_PASSWORD` will now be derived from the username part of the Wyze email address instead of using a randomly generated password.
  - Example: For the email address `john123@doe.com`, the `WB_PASSWORD` will be `john123`.
- Default `WB_API` will be based on the wyze account for persistance.

### Stream Authentication

NEW: `STREAM_AUTH` option to specify multiple users and paths:

- Username and password should be separated by a `:`
- An additional `:` can be used to specify the allowed IP address for the user.
  - **This does NOT work with docker desktop**
  - Specify multiple IPs using a comma
- Use the `@` to specify paths accessible to the user.
  - Paths are optional for each user.  
  - Multiple paths can be specified by using a comma. If none are provided, the user will have access to all paths/streams
- Multiple users can be specified by using  `|` as a separator

  **EXAMPLE**:

```yaml
  STREAM_AUTH=user:pass@cam-1,other-cam|second-user:password@just-one-cam|user3:pass
```

- `user:pass`  has access to `cam-1` and `other-cam`
- `second-user:password` has access to `just-one-cam`
- `user3:pass` has access to **all** paths/cameras

  See [Wiki](https://github.com/mrlt8/docker-wyze-bridge/wiki/Authentication#custom-stream-auth) for more information and examples.

### Recording via MediaMTX

Recoding streams has been updated to use MediaMTX with the option to delete older clips.

Use `RECORD_ALL` or `RECORD_CAM_NAME` to enable recording.

- `RECORD_FILE_NAME` Available variables are `%path`, `{CAM_NAME}`, `{cam_name}`, `%Y` `%m` `%d` `%H` `%M` `%S` `%f` `%s` (time in strftime format).
- `RECORD_PATH` Available variables are `%path`, `{CAM_NAME}`, `{cam_name}`, `%Y` `%m` `%d` `%H` `%M` `%S` `%f` `%s` (time in strftime format).
- `RECORD_LENGTH` Length of each clip. Use `s` for seconds , `h` for hours. Defaults to `60s`
- `RECORD_KEEP` Delete older clips. Use `s` for seconds , `h` for hours. Set to 0s to disable automatic deletion. Defaults to `0s`

Note that as of release v3.10.0, which uses *mediaMTX 1.12.0*, requires the combination of your `RECORD_FILE_NAME` and `RECORD_PATH` settings
specifying recording's file complete path **MUST** reference **ALL** of `%Y` `%m` `%d` `%H` `%M` `%S` tokens, for example:
`RECORD_FILE_NAME = "%H%M%S%"` and `RECORD_PATH_NAME = "{path}/{cam_name}/%Y/%m/%d%"` would be valid. You can also just
ensure the combined path includes `%s` (which is the unix epoch value as an integer).

[View previous changes](https://github.com/waelsamy/docker-wyze-bridge/releases)

## FAQ

- How does this work?
  - It uses the same SDK as the app to communicate directly with the cameras. See [kroo/wyzecam](https://github.com/kroo/wyzecam) for details.
- Does it use internet bandwidth when streaming?
  - Not in most cases. The bridge will attempt to stream locally if possible but will fallback to streaming over the internet if you're trying to stream from a different location or from a shared camera. See the [wiki](https://github.com/mrlt8/docker-wyze-bridge/wiki/Network-Connection-Modes) for more details.
- Can this work offline/can I block all wyze services?
  - No. Streaming should continue to work without an active internet connection, but will probably stop working after some time as the cameras were not designed to be used without the cloud. Some camera commands also depend on the cloud and may not function without an active connection. See [wz_mini_hacks](https://github.com/gtxaspec/wz_mini_hacks/wiki/Configuration-File#self-hosted--isolated-mode) for firmware level modification to run the camera offline.
- Why aren't all wyze cams supported yet (OG/Doorbell Pro)?
  - These cameras are using a different SDK and will require a different method to connect and stream. See the awesome [cryze](https://github.com/carTloyal123/cryze) project by @carTloyal123.

## Compatibility

![Supports arm32v7 Architecture](https://img.shields.io/badge/arm32v7-yes-success.svg)
![Supports arm64 Architecture](https://img.shields.io/badge/arm64-yes-success.svg)
![Supports amd64 Architecture](https://img.shields.io/badge/amd64-yes-success.svg)
![Supports Apple Silicon Architecture](https://img.shields.io/badge/apple_silicon-yes-success.svg)

[![Home Assistant Add-on](https://img.shields.io/badge/home_assistant-add--on-blue.svg?logo=homeassistant&logoColor=white)](https://github.com/waelsamy/docker-wyze-bridge/wiki/Home-Assistant)
[![Homebridge](https://img.shields.io/badge/homebridge-camera--ffmpeg-blue.svg?logo=homebridge&logoColor=white)](https://sunoo.github.io/homebridge-camera-ffmpeg/configs/WyzeCam.html)
[![Portainer stack](https://img.shields.io/badge/portainer-stack-blue.svg?logo=portainer&logoColor=white)](https://github.com/mrlt8/docker-wyze-bridge/wiki/Portainer)
[![Unraid Community App](https://img.shields.io/badge/unraid-community--app-blue.svg?logo=unraid&logoColor=white)](https://github.com/mrlt8/docker-wyze-bridge/issues/236)

Should work on most x64 systems as well as on most modern arm-based systems like the Raspberry Pi 3/4/5 or Apple Silicon M1/M2/M3.

The container can be run on its own, in [Portainer](https://github.com/mrlt8/docker-wyze-bridge/wiki/Portainer), [Unraid](https://github.com/mrlt8/docker-wyze-bridge/issues/236), as a [Home Assistant Add-on](https://github.com/mrlt8/docker-wyze-bridge/wiki/Home-Assistant), locally or remotely in the cloud.

### Ubiquiti Unifi

> [!NOTE]  
> Some network adjustments may be needed - see [this discussion](https://github.com/mrlt8/docker-wyze-bridge/discussions/891) for more information.

## Supported Cameras

> [!IMPORTANT]
> Some newer camera firmware versions may cause issues with remote access via P2P. Local "LAN" access seems unaffected at this time. A temporary solution is to use a VPN. See the [OpenVPN example](https://github.com/waelsamy/docker-wyze-bridge/blob/main/docker-compose.ovpn.yml).

| Camera                        | Model          | Tutk Support                                                  | Latest FW |
| ----------------------------- | -------------- | ------------------------------------------------------------- | --------- |
| Wyze Cam v1 [HD only]         | WYZEC1         | ✅                                                            | 3.9.4.x   |
| Wyze Cam V2                   | WYZEC1-JZ      | ✅                                                            | 4.9.9.x   |
| Wyze Cam V3                   | WYZE_CAKP2JFUS | ✅                                                            | 4.36.11.x |
| Wyze Cam V4 [2K]              | HL_CAM4        | ✅                                                            | 4.52.3.x  |
| Wyze Cam Floodlight           | WYZE_CAKP2JFUS | ✅                                                            | 4.36.11.x |
| Wyze Cam Floodlight V2 [2k]   | HL_CFL2        | ✅                                                            | 4.53.2.x  |
| Wyze Cam V3 Pro [2K]          | HL_CAM3P       | ✅                                                            | 4.58.11.x |
| Wyze Cam Pan                  | WYZECP1_JEF    | ✅                                                            | 4.10.9.x  |
| Wyze Cam Pan v2               | HL_PAN2        | ✅                                                            | 4.49.11.x |
| Wyze Cam Pan v3               | HL_PAN3        | ✅                                                            | 4.50.4.x  |
| Wyze Cam Pan Pro [2K]         | HL_PANP        | ✅                                                            | -         |
| Wyze Cam Outdoor              | WVOD1          | ✅                                                            | 4.17.4.x  |
| Wyze Cam Outdoor v2           | HL_WCO2        | ✅                                                            | 4.48.4.x  |
| Wyze Cam Doorbell             | WYZEDB3        | ✅                                                            | 4.25.1.x  |
| Wyze Cam Doorbell v2 [2K]     | HL_DB2         | ✅                                                            | 4.51.1.x  |
| Wyze Cam Doorbell Pro 2       | AN_RDB1        | ❓                                                            | -         |
| Wyze Battery Cam Pro          | AN_RSCW        | [⚠️](https://github.com/mrlt8/docker-wyze-bridge/issues/1011) | -         |
| Wyze Cam Flood Light Pro [2K] | LD_CFP         | [⚠️](https://github.com/mrlt8/docker-wyze-bridge/issues/822)  | -         |
| Wyze Cam Doorbell Pro         | GW_BE1         | [⚠️](https://github.com/mrlt8/docker-wyze-bridge/issues/276)  | -         |
| Wyze Cam OG                   | GW_GC1         | [⚠️](https://github.com/mrlt8/docker-wyze-bridge/issues/677)  | -         |
| Wyze Cam OG Telephoto 3x      | GW_GC2         | [⚠️](https://github.com/mrlt8/docker-wyze-bridge/issues/677)  | -         |

## Basic Usage

### docker-compose (recommended)

This is similar to the docker run command, but will save all your options in a yaml file.

1. Install [Docker Compose](https://docs.docker.com/compose/install/).
2. Use the [sample](https://raw.githubusercontent.com/waelsamy/docker-wyze-bridge/main/docker-compose.sample.yml) as a guide to create a `docker-compose.yml` file with your wyze credentials.
3. Run `docker-compose up`.

Once you're happy with your config you can use `docker-compose up -d` to run it in detached mode.

> [!CAUTION]
> If your credentials contain a `$` character, you need to escape it with another `$` sign (e.g., `pa$$word` > `pa$$$$word`) or leave your credentials blank and use the webUI to login.
>
> [!NOTE]
> You may need to [update the WebUI links](https://github.com/mrlt8/docker-wyze-bridge/wiki/WebUI#custom-ports) if you're changing the ports or using a reverse proxy.

#### Updating your container

To update your container, `cd` into the directory where your `docker-compose.yml` is located and run:

```bash
docker-compose pull # Pull new image
docker-compose up -d # Restart container in detached mode
docker image prune # Remove old images
```

### 🏠 Home Assistant

Visit the [wiki page](https://github.com/mrlt8/docker-wyze-bridge/wiki/Home-Assistant) for additional information on Home Assistant.

[![Open your Home Assistant instance and show the add add-on repository dialog with a specific repository URL pre-filled.](https://my.home-assistant.io/badges/supervisor_add_addon_repository.svg)](https://my.home-assistant.io/redirect/supervisor_add_addon_repository/?repository_url=https%3A%2F%2Fgithub.com%2Fidisposable%2Fdocker-wyze-bridge)

## Additional Info

- [Camera Commands (MQTT/REST API)](https://github.com/mrlt8/docker-wyze-bridge/wiki/Camera-Commands)
- [Two-Factor Authentication (2FA/MFA)](https://github.com/mrlt8/docker-wyze-bridge/wiki/Two-Factor-Authentication)
- [ARM/Apple Silicon/Raspberry Pi](https://github.com/mrlt8/docker-wyze-bridge/wiki/Raspberry-Pi-and-Apple-Silicon-(arm-arm64-m1-m2-m3))
- [Network Connection Modes](https://github.com/mrlt8/docker-wyze-bridge/wiki/Network-Connection-Modes)
- [Portainer](https://github.com/mrlt8/docker-wyze-bridge/wiki/Portainer)
- [Unraid](https://github.com/mrlt8/docker-wyze-bridge/issues/236)
- [Home Assistant](https://github.com/mrlt8/docker-wyze-bridge/wiki/Home-Assistant)
- [Homebridge Camera FFmpeg](https://homebridge-plugins.github.io/homebridge-camera-ffmpeg/configs/WyzeCam.html)
- [HomeKit Secure Video](https://github.com/mrlt8/docker-wyze-bridge/wiki/HomeKit-Secure-Video)
- [WebUI API](https://github.com/mrlt8/docker-wyze-bridge/wiki/WebUI-API)

## Web-UI

The bridge features a basic Web-UI which can display a preview of all your cameras as well as direct links to all the video streams.

The web-ui can be accessed on the default port `5000`:

```http
http://localhost:5000/
```

See also:

- [WebUI page](https://github.com/mrlt8/docker-wyze-bridge/wiki/WebUI)
- [WebUI API page](https://github.com/mrlt8/docker-wyze-bridge/wiki/WebUI-API)

## WebRTC

WebRTC should work automatically in Home Assistant mode, however, some additional configuration is required to get WebRTC working in the standard docker mode.

- WebRTC requires two additional ports to be configured in docker:

```yaml
ports:
  - 8889:8889 #WebRTC
  - 8189:8189/udp # WebRTC/ICE
```

- In addition, the `WB_IP` env needs to be set with the IP address of the server running the bridge.

```yaml
environment:
  - WB_IP=192.168.1.116
```

- See [documentation](https://github.com/aler9/rtsp-simple-server#usage-inside-a-container-or-behind-a-nat) for additional information/options.

## Advanced Options

All environment variables are optional.

- [Audio](https://github.com/mrlt8/docker-wyze-bridge/wiki/Camera-Audio)
- [Bitrate and Resolution](https://github.com/mrlt8/docker-wyze-bridge/wiki/Camera-Bitrate-and-Resolution)
- [Camera Substreams](https://github.com/mrlt8/docker-wyze-bridge/wiki/Camera-Substreams)
- [MQTT Configuration](https://github.com/mrlt8/docker-wyze-bridge/wiki/Advanced-Option#mqtt-config)
- [Filtering Cameras](https://github.com/mrlt8/docker-wyze-bridge/wiki/Camera-Filtering)
- [Doorbell/Camera Rotation](https://github.com/mrlt8/docker-wyze-bridge/wiki/Doorbell-and-Camera-Rotation)
- [Custom FFmpeg Commands](https://github.com/mrlt8/docker-wyze-bridge/wiki/Advanced-Option#custom-ffmpeg-commands)
- [Interval Snapshots](https://github.com/mrlt8/docker-wyze-bridge/wiki/Advanced-Option#snapshotstill-images)
- [Stream Recording and Livestreaming](https://github.com/mrlt8/docker-wyze-bridge/wiki/Stream-Recording-and-Livestreaming)
- [rtsp-simple-server/MediaMTX Config](https://github.com/mrlt8/docker-wyze-bridge/wiki/Advanced-Option#mediamtx)
- [Offline/IFTTT Webhook](https://github.com/mrlt8/docker-wyze-bridge/wiki/Advanced-Option#offline-camera-ifttt-webhook)
- [Proxy Stream from RTSP Firmware](https://github.com/mrlt8/docker-wyze-bridge/wiki/Advanced-Option#proxy-stream-from-rtsp-firmware)
- [BOA HTTP Server/Motion Alerts](https://github.com/mrlt8/docker-wyze-bridge/wiki/Boa-HTTP-Server)
- [Debugging Options](https://github.com/mrlt8/docker-wyze-bridge/wiki/Advanced-Option#debugging-options)

## Other Wyze Projects

Honorable Mentions:

- [@noelhibbard's script](https://gist.github.com/noelhibbard/03703f551298c6460f2fd0bfdbc328bd#file-readme-md) - Original script that the bridge is bassd on.
- [kroo/wyzecam](https://github.com/kroo/wyzecam) - Original library that the bridge is based on.

Video Streaming:

- [gtxaspec/wz_mini_hacks](https://github.com/gtxaspec/wz_mini_hacks) - Firmware level modification for Ingenic based cameras with an RTSP server and [self-hosted mode](https://github.com/gtxaspec/wz_mini_hacks/wiki/Configuration-File#self-hosted--isolated-mode) to use the cameras without the wyze services.
- [thingino](https://github.com/themactep/thingino-firmware) - Advanced custom firmware for some Ingenic-based wyze cameras.
- [carTloyal123/cryze](https://github.com/carTloyal123/cryze) - Stream video from wyze cameras (Gwell cameras) that use the Iotvideo SDK from Tencent Cloud.
- [xerootg/cryze_v2](https://github.com/xerootg/cryze_v2) - Stream video from wyze cameras (Gwell cameras) that use the Iotvideo SDK from Tencent Cloud.
- [mnakada/atomcam_tools](https://github.com/mnakada/atomcam_tools) - Video streaming for Wyze v3.

General Wyze:

- [shauntarves/wyze-sdk](https://github.com/shauntarves/wyze-sdk) - python library to interact with wyze devices over the cloud.
