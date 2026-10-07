# Skillry Storage for macOS

Native macOS 13+ menu bar companion for the optional `skillry-storage` engine. It reads JSON status, shows disk and queue state, and sends explicit actions to the same engine. It is a separate opt-in app, not part of Skillry's portable skills and agents installer.

Build on macOS with Xcode Command Line Tools:

```sh
./apps/storage-companion/build.sh
```

The script writes `apps/storage-companion/build/Skillry Storage.app` by default. Pass an output directory to build elsewhere, for example `./apps/storage-companion/build.sh /tmp/skillry-storage-build.noindex`; the result is `/tmp/skillry-storage-build.noindex/Skillry Storage.app`. The output bundle must not already exist. Each build gets a numeric timestamp in `CFBundleVersion`. The script includes the public Python engine as a fallback and ad-hoc signs the local bundle. Move the bundle to the chosen canonical Applications location only when you choose to install it. The app first uses `~/.local/bin/skillry-storage` if present; otherwise it runs its bundled engine through `python3 -B`. Python bytecode writes are disabled for both routes. No web service, package download, cron job, or independent worker is installed.

The default configuration is `~/.config/skillry/storage.json`. Settings can select an existing profile or set roots, an intake folder, and a local or SSH archive target. A single native control window appears on first launch, reopens when Finder opens the running app again, and is also available from the menu's Ayarlar button. Automatic cleanup and archiving remain off until enabled in the selected engine profile. The app's single 60-second timer asks the engine to tick; the engine owns the process lock and safety checks. Closing the control window or menu does not cancel ongoing work. Pause and resume wait for the engine's state response. Login start uses macOS Login Items through `SMAppService.mainApp`.

For an already authorized user-session installation, launching the installed app once with `--enable-login` requests `SMAppService.mainApp` registration. A later normal launch does not repeat that request. If macOS requires approval, Settings reports that state and opens the system Login Items panel on request; it does not claim automatic launch is active until the system reports `enabled`.

The Jev SecureField saves a generic password in macOS Keychain under the engine's configured service and account, matching the existing Jev reference. The app never places the key in process arguments, the JSON configuration, or logs. macOS may ask the user to grant this signed app access to an existing Keychain item.

Status and previews are engine facts. Candidate bytes describe possible output size; `freed_bytes` is the engine's measured increase in free space and may be unavailable before any measured operation. Cleanup and app package actions require a fresh preview and a separate menu confirmation. Missing engine, disconnected target, empty queues, and failed actions are shown as such. A menu timer does not end an in-progress archive: only status and configuration read probes have frontend timeouts; the engine owns mutation deadlines and cancellation.

The inbox distinguishes verified archives from pending catalog links and shows catalog errors. If the original file is gone, Open calls `inbox retrieve --id` and opens only the engine's verified local cache path; remote archive paths are never opened as local files.
