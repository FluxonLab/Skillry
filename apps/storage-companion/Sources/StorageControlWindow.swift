import AppKit
import SwiftUI

@MainActor
final class StorageControlWindow {
    static let shared = StorageControlWindow()
    private var window: NSWindow?

    func show() {
        if window == nil {
            let created = NSWindow(
                contentRect: NSRect(x: 0, y: 0, width: 620, height: 650),
                styleMask: [.titled, .closable, .miniaturizable, .resizable],
                backing: .buffered,
                defer: false
            )
            created.title = "Skillry Storage"
            created.contentViewController = NSHostingController(
                rootView: SettingsView(model: StorageModel.shared)
                    .frame(minWidth: 560, minHeight: 550)
            )
            created.isReleasedWhenClosed = false
            created.center()
            created.setFrameAutosaveName("SkillryStorageControlWindow")
            window = created
        }
        window?.makeKeyAndOrderFront(nil)
        NSApp.activate(ignoringOtherApps: true)
    }
}

@MainActor
final class StorageAppDelegate: NSObject, NSApplicationDelegate {
    private let firstWindowKey = "SkillryStorageHasShownControlWindow"

    func applicationDidFinishLaunching(_ notification: Notification) {
        if CommandLine.arguments.contains("--show-settings") || !UserDefaults.standard.bool(forKey: firstWindowKey) {
            StorageControlWindow.shared.show()
            UserDefaults.standard.set(true, forKey: firstWindowKey)
        }
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        StorageControlWindow.shared.show()
        return false
    }
}
