import AppKit
import ServiceManagement
import SwiftUI
import UniformTypeIdentifiers

struct SettingsView: View {
    @ObservedObject var model: StorageModel
    @State private var intake = ""
    @State private var roots = ""
    @State private var applicationRoots = ""
    @State private var archiveKind = "none"
    @State private var archiveRoot = ""
    @State private var sshAlias = ""
    @State private var receiverCommand = ""
    @State private var automaticCleanup = false
    @State private var automaticArchive = false
    @State private var graceHours = "24"
    @State private var settleSeconds = "120"
    @State private var key = ""
    @State private var jevEnabled = false
    @State private var jevHelper = ""
    @State private var canonicalBundle = ""
    @State private var canonicalPath = ""
    @State private var rollbackPath = ""
    @State private var selectedConfig = ""
    @State private var loginEnabled = false
    @State private var validationError: String?
    @State private var hydratedForPath: String?

    var body: some View {
        Form {
            Section("Profil") {
                HStack {
                    TextField("Yapılandırma dosyası", text: $selectedConfig)
                        .textFieldStyle(.roundedBorder)
                    Button("Seç") { chooseConfig() }
                    Button("Aç") { Task { await model.switchConfig(to: expanded(selectedConfig)) } }
                        .disabled(selectedConfig.isEmpty || model.busy)
                }
                if !discoveredConfigs.isEmpty {
                    Picker("Bulunan profiller", selection: $selectedConfig) {
                        ForEach(discoveredConfigs, id: \.self) { Text($0).tag($0) }
                    }
                }
                Text("Mevcut profil seçildiğinde kayıtlı kurallar ve durum motordan okunur.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            Section("İzlenecek alanlar") {
                pathField("Gelenler klasörü", text: $intake)
                VStack(alignment: .leading) {
                    Text("Çalışma kökleri (her satıra bir yol)")
                    TextEditor(text: $roots).font(.system(.body, design: .monospaced)).frame(height: 72)
                    Button("Kök ekle") { if let path = chooseFolder() { roots = appended(path, to: roots) } }
                }
                VStack(alignment: .leading) {
                    Text("Uygulama kökleri (her satıra bir yol)")
                    TextEditor(text: $applicationRoots).font(.system(.body, design: .monospaced)).frame(height: 60)
                    Button("Kök ekle") { if let path = chooseFolder() { applicationRoots = appended(path, to: applicationRoots) } }
                }
            }
            Section("Arşiv hedefi") {
                Picker("Tür", selection: $archiveKind) {
                    Text("Yok").tag("none")
                    Text("Yerel klasör").tag("local")
                    Text("SSH alıcısı").tag("ssh")
                }
                if archiveKind == "local" { pathField("Arşiv klasörü", text: $archiveRoot) }
                if archiveKind == "ssh" {
                    TextField("Alıcıdaki mutlak arşiv yolu", text: $archiveRoot)
                    TextField("SSH takma adı", text: $sshAlias)
                    TextField("Alıcı komutu", text: $receiverCommand)
                    Text("Bağlantı ve erişim mevcut SSH yapılandırmasından gelir.")
                        .font(.caption).foregroundStyle(.secondary)
                }
            }
            Section("Canonical uygulama") {
                let roles = model.config["applications"] as? [String: Any] ?? [:]
                ForEach(roles.keys.sorted(), id: \.self) { bundle in
                    HStack {
                        Text(bundle)
                        Spacer()
                        Button("Düzenle") {
                            canonicalBundle = bundle
                            if let role = roles[bundle] as? [String: Any] {
                                canonicalPath = Display.text(role, "canonical", fallback: "")
                                rollbackPath = Display.text(role, "rollback", fallback: "")
                            } else {
                                canonicalPath = roles[bundle] as? String ?? ""
                                rollbackPath = ""
                            }
                        }
                    }.font(.caption)
                }
                TextField("Bundle ID (ör. org.example.app)", text: $canonicalBundle)
                HStack {
                    TextField("Tek güncel .app yolu", text: $canonicalPath)
                    Button("Seç") { if let path = chooseApplication() { canonicalPath = path } }
                }
                HStack {
                    TextField("Geri dönüş .app yolu (isteğe bağlı)", text: $rollbackPath)
                    Button("Seç") { if let path = chooseApplication() { rollbackPath = path } }
                }
                Button("Uygulama rolünü kaydet") { saveCanonicalApplication() }
                    .disabled(canonicalBundle.isEmpty || canonicalPath.isEmpty || !canSaveProfile)
                Text("Bu seçim tek başına paket silmez; aday paketler ayrıca işaretlenir ve önizlenir.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            Section("Otomasyon") {
                Toggle("Kayıtlı, kapanmış işlerin uygun çıktılarını otomatik temizle", isOn: $automaticCleanup)
                Toggle("Tamamlanan Gelenler dosyalarını arşivle", isOn: $automaticArchive)
                HStack {
                    TextField("Yerel bekleme (saat)", text: $graceHours).frame(width: 100)
                    TextField("Dosya sakinleşme süresi (saniye)", text: $settleSeconds).frame(width: 120)
                }
                Button("Kuralları kaydet") { saveConfig() }.disabled(!canSaveProfile)
                Toggle("Oturum açılışında başlat", isOn: $loginEnabled)
                    .onChange(of: loginEnabled) { newValue in
                        if newValue != model.launchAtLogin {
                            model.setLaunchAtLogin(newValue)
                            loginEnabled = model.launchAtLogin
                        }
                    }
                LabeledContent("macOS durumu", value: model.loginStatusText)
                if model.loginStatus == .requiresApproval {
                    Button("Oturum Açma Öğeleri ayarlarını aç") {
                        SMAppService.openSystemSettingsLoginItems()
                    }
                    Text("Kayıt yapıldı; macOS onayı verilene kadar otomatik açılış etkin görünmez.")
                        .font(.caption).foregroundStyle(.secondary)
                }
                Text("Otomatik işlerin durumu menüdeki Duraklat / Devam et denetiminden yönetilir.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            Section("Jev") {
                LabeledContent("Bağlantı", value: Display.text(model.jev, "state"))
                LabeledContent("Etkin", value: model.jev["enabled"] as? Bool == true ? "Evet" : "Hayır")
                LabeledContent("Yardımcı", value: Display.text(model.jev, "helper_path"))
                LabeledContent("Gizli anahtar kaynağı", value: "Keychain · \(Display.text(model.jev, "service")) / \(Display.text(model.jev, "account"))")
                LabeledContent("Son durum", value: Display.text(model.jev, "last_status"))
                Toggle("Jev önerilerini etkinleştir", isOn: $jevEnabled)
                HStack {
                    TextField("Jev yardımcı programı", text: $jevHelper)
                    Button("Seç") { if let path = chooseFile() { jevHelper = path } }
                }
                SecureField("Yeni Jev anahtarı", text: $key)
                Button("Anahtarı Keychain'e kaydet") {
                    let value = key
                    key = ""
                    Task { await model.saveJevKey(value) }
                }.disabled(key.isEmpty || !canSaveProfile)
                Text("Anahtar yapılandırma dosyasına, komut satırına veya günlüğe yazılmaz. Mevcut değer gösterilmez.")
                    .font(.caption).foregroundStyle(.secondary)
            }
            Section("Yardımcı araçlar") {
                if model.tools.isEmpty {
                    Text("Motor henüz araç durumu bildirmedi.").foregroundStyle(.secondary)
                }
                ForEach(model.tools.indices, id: \.self) { index in
                    let item = model.tools[index]
                    HStack {
                        Text(Display.text(item, "id"))
                        Spacer()
                        Text(item["available"] as? Bool == true ? "Kullanılabilir" : Display.text(item, "reason", fallback: "Bulunamadı"))
                            .foregroundStyle(.secondary)
                    }
                }
            }
            if let error = validationError ?? model.errorMessage { Text(error).foregroundStyle(.red) }
            if let message = model.message { Text(message).foregroundStyle(.green) }
        }
        .formStyle(.grouped)
        .onAppear {
            selectedConfig = model.configPath
            model.refreshLoginStatus()
            loginEnabled = model.launchAtLogin
            hydrateIfNeeded()
        }
        .onChange(of: model.configPath) { _ in
            selectedConfig = model.configPath
            hydratedForPath = nil
            hydrateIfNeeded()
        }
        .onChange(of: model.loadedConfigPath) { _ in hydrateIfNeeded() }
        .onReceive(NotificationCenter.default.publisher(for: NSApplication.didBecomeActiveNotification)) { _ in
            model.refreshLoginStatus()
            loginEnabled = model.launchAtLogin
        }
    }

    private var discoveredConfigs: [String] {
        let home = FileManager.default.homeDirectoryForCurrentUser
        let folders = [home.appendingPathComponent(".config/skillry"),
                       home.appendingPathComponent(".skillry/profiles")]
        var found = Set<String>()
        for folder in folders {
            if let enumerator = FileManager.default.enumerator(at: folder, includingPropertiesForKeys: nil,
                                                               options: [.skipsHiddenFiles, .skipsPackageDescendants]) {
                for case let url as URL in enumerator where url.pathExtension == "json" &&
                    (url.lastPathComponent == "storage.json" || url.lastPathComponent.hasPrefix("storage-")) {
                    found.insert(url.path)
                }
            }
        }
        found.insert(model.configPath)
        return found.sorted()
    }

    private var canSaveProfile: Bool {
        hydratedForPath == model.configPath && model.loadedConfigPath == model.configPath && !model.busy
    }

    private func hydrateIfNeeded() {
        guard hydratedForPath != model.configPath,
              model.loadedConfigPath == model.configPath,
              model.status["config"] is [String: Any] else { return }
        loadFromModel()
    }

    private func loadFromModel() {
        selectedConfig = model.configPath
        let config = model.config
        intake = Display.text(config, "intake_dir", fallback: FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent("Gelenler").path)
        roots = (config["workspace_roots"] as? [String] ?? []).joined(separator: "\n")
        applicationRoots = (config["application_roots"] as? [String] ?? []).joined(separator: "\n")
        let archive = config["archive"] as? [String: Any] ?? [:]
        archiveKind = Display.text(archive, "kind", fallback: "none")
        archiveRoot = Display.text(archive, "root", fallback: "")
        sshAlias = Display.text(archive, "ssh_alias", fallback: "")
        receiverCommand = Display.text(archive, "receiver_command", fallback: "")
        automaticCleanup = config["automatic_cleanup"] as? Bool ?? false
        automaticArchive = config["automatic_archive"] as? Bool ?? false
        let jevConfig = config["jev"] as? [String: Any] ?? [:]
        jevEnabled = jevConfig["enabled"] as? Bool ?? false
        jevHelper = Display.text(jevConfig, "helper_path", fallback: "")
        let grace = (config["local_grace_seconds"] as? NSNumber)?.doubleValue ?? 86_400
        graceHours = String(Int(grace / 3600))
        settleSeconds = String((config["settle_seconds"] as? NSNumber)?.intValue ?? 120)
        loginEnabled = model.launchAtLogin
        hydratedForPath = model.configPath
    }

    private func saveConfig() {
        guard let hours = Double(graceHours), hours >= 0,
              let settle = Int(settleSeconds), settle >= 0 else {
            validationError = "Bekleme süreleri sıfır veya pozitif sayı olmalı."
            return
        }
        validationError = nil
        var archive: [String: Any] = model.config["archive"] as? [String: Any] ?? [:]
        archive["kind"] = archiveKind
        if archiveKind == "local" { archive["root"] = expanded(archiveRoot) }
        if archiveKind == "ssh" {
            archive["root"] = archiveRoot.trimmingCharacters(in: .whitespacesAndNewlines)
            archive["ssh_alias"] = sshAlias.trimmingCharacters(in: .whitespacesAndNewlines)
            archive["receiver_command"] = receiverCommand.trimmingCharacters(in: .whitespacesAndNewlines)
        }
        let patch: [String: Any] = [
            "intake_dir": expanded(intake),
            "workspace_roots": lines(roots),
            "application_roots": lines(applicationRoots),
            "archive": archive,
            "automatic_cleanup": automaticCleanup,
            "automatic_archive": automaticArchive,
            "local_grace_seconds": Int(hours * 3600),
            "settle_seconds": settle
        ]
        var completePatch = patch
        completePatch["jev"] = ["enabled": jevEnabled,
                                "helper_path": jevHelper.isEmpty ? NSNull() : expanded(jevHelper)] as [String: Any]
        Task {
            await model.run(["config", "set"], input: completePatch, success: "Ayarlar kaydedildi.")
            if model.message == "Ayarlar kaydedildi." && model.loadedConfigPath == model.configPath {
                loadFromModel()
            }
        }
    }

    private func pathField(_ label: String, text: Binding<String>) -> some View {
        HStack {
            TextField(label, text: text)
            Button("Seç") { if let path = chooseFolder() { text.wrappedValue = path } }
        }
    }

    private func chooseFolder() -> String? {
        let panel = NSOpenPanel()
        panel.canChooseFiles = false
        panel.canChooseDirectories = true
        panel.allowsMultipleSelection = false
        return panel.runModal() == .OK ? panel.url?.path : nil
    }

    private func chooseConfig() {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowedContentTypes = [.json]
        if panel.runModal() == .OK, let path = panel.url?.path { selectedConfig = path }
    }

    private func chooseFile() -> String? {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        return panel.runModal() == .OK ? panel.url?.path : nil
    }

    private func chooseApplication() -> String? {
        let panel = NSOpenPanel()
        panel.canChooseFiles = true
        panel.canChooseDirectories = false
        panel.allowedContentTypes = [UTType(filenameExtension: "app") ?? .bundle]
        return panel.runModal() == .OK ? panel.url?.path : nil
    }

    private func saveCanonicalApplication() {
        let bundle = canonicalBundle.trimmingCharacters(in: .whitespacesAndNewlines)
        let canonical = expanded(canonicalPath)
        guard !bundle.isEmpty, canonical.hasPrefix("/") else {
            validationError = "Bundle ID ve mutlak uygulama yolu gerekli."
            return
        }
        var applications = model.config["applications"] as? [String: Any] ?? [:]
        var role: [String: Any] = ["canonical": canonical]
        if !rollbackPath.isEmpty { role["rollback"] = expanded(rollbackPath) }
        applications[bundle] = role
        validationError = nil
        Task { await model.run(["config", "set"], input: ["applications": applications], success: "Uygulama rolü kaydedildi.") }
    }

    private func expanded(_ path: String) -> String {
        (path as NSString).expandingTildeInPath
    }

    private func lines(_ source: String) -> [String] {
        source.split(whereSeparator: \.isNewline).map { expanded(String($0).trimmingCharacters(in: .whitespaces)) }
            .filter { !$0.isEmpty }
    }

    private func appended(_ path: String, to value: String) -> String {
        value.isEmpty ? path : value + "\n" + path
    }
}
