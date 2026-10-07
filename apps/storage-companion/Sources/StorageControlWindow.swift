import AppKit
import SwiftUI

enum StorageControlTab: Hashable {
    case dashboard
    case settings
}

private struct StorageControlView: View {
    @ObservedObject var controller: StorageControlWindow
    @ObservedObject var model: StorageModel

    var body: some View {
        TabView(selection: $controller.selectedTab) {
            StorageMenuView(model: model) { controller.show(tab: .settings) }
                .tabItem { Label("Kontrol", systemImage: "externaldrive") }
                .tag(StorageControlTab.dashboard)
            SettingsView(model: model)
                .tabItem { Label("Ayarlar", systemImage: "gearshape") }
                .tag(StorageControlTab.settings)
        }
        .frame(minWidth: 650, minHeight: 700)
    }
}

@MainActor
final class StorageControlWindow: ObservableObject {
    static let shared = StorageControlWindow()
    @Published var selectedTab: StorageControlTab = .dashboard
    private var window: NSWindow?

    func show(tab: StorageControlTab = .dashboard) {
        selectedTab = tab
        if window == nil {
            let created = NSWindow(
                contentRect: NSRect(x: 0, y: 0, width: 700, height: 750),
                styleMask: [.titled, .closable, .miniaturizable, .resizable],
                backing: .buffered,
                defer: false
            )
            created.title = "Skillry Storage"
            created.contentViewController = NSHostingController(
                rootView: StorageControlView(controller: self, model: StorageModel.shared)
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
        if CommandLine.arguments.contains("--enable-login") {
            StorageModel.shared.enableLoginFromLaunch()
        }
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
