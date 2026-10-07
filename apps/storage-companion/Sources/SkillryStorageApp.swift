import AppKit
import SwiftUI

@main
struct SkillryStorageApp: App {
    @NSApplicationDelegateAdaptor(StorageAppDelegate.self) private var appDelegate
    @StateObject private var model = StorageModel.shared

    var body: some Scene {
        MenuBarExtra("Skillry Storage", systemImage: "externaldrive") {
            StorageMenuView(model: model)
        }
        .menuBarExtraStyle(.window)
    }
}

private enum Section: String, CaseIterable {
    case overview = "Durum"
    case cleanup = "Temizlik"
    case inbox = "Gelenler"
    case workspaces = "Projeler"
    case applications = "Uygulamalar"
}

struct StorageMenuView: View {
    @ObservedObject var model: StorageModel
    @State private var section: Section = .overview
    @State private var cleanupPlan: [String: Any]?
    @State private var appPlan: [String: Any]?
    @State private var confirmCleanup = false
    @State private var confirmApps = false

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 2) {
                    Text("Skillry Storage").font(.headline)
                    Text(model.hasStatus ? (model.paused ? "Otomasyon duraklatıldı" : "Otomasyon çalışıyor") : "Durum bekleniyor")
                        .font(.caption).foregroundStyle(model.paused ? Color.orange : Color.secondary)
                }
                Spacer()
                if model.loading || model.busy { ProgressView().controlSize(.small) }
                Button { Task { await model.refresh() } } label: { Image(systemName: "arrow.clockwise") }
                    .help("Durumu yenile")
                    .disabled(model.busy)
            }
            Picker("Bölüm", selection: $section) {
                ForEach(Section.allCases, id: \.self) { value in Text(value.rawValue).tag(value) }
            }
            .pickerStyle(.segmented)
            .labelsHidden()

            if let error = model.errorMessage {
                Label(error, systemImage: "exclamationmark.triangle")
                    .foregroundStyle(.red).font(.callout)
                    .fixedSize(horizontal: false, vertical: true)
            }
            if let message = model.message {
                Label(message, systemImage: "checkmark.circle")
                    .foregroundStyle(.green).font(.callout)
            }
            if !model.hasStatus {
                VStack(spacing: 8) {
                    Image(systemName: "externaldrive.badge.questionmark").font(.largeTitle)
                    Text("Durum alınamadı").font(.headline)
                    Text("Motor veya profil erişilebilir olduğunda burada gerçek durum görünecek.")
                        .font(.callout).foregroundStyle(.secondary).multilineTextAlignment(.center)
                }.frame(maxWidth: .infinity, maxHeight: .infinity)
            } else {
                ScrollView {
                    VStack(alignment: .leading, spacing: 14) {
                        switch section {
                        case .overview: overview
                        case .cleanup: cleanup
                        case .inbox: inbox
                        case .workspaces: workspaces
                        case .applications: applications
                        }
                    }
                    .frame(maxWidth: .infinity, alignment: .leading)
                }
            }
            Divider()
            HStack {
                Text("Son güncelleme: \(model.lastUpdated?.formatted(date: .omitted, time: .shortened) ?? "—")")
                    .font(.caption).foregroundStyle(.secondary)
                Spacer()
                Button("Ayarlar") { StorageControlWindow.shared.show() }
                Button(model.paused ? "Devam et" : "Duraklat") {
                    Task { await model.run([model.paused ? "resume" : "pause"], success: model.paused ? "Motor devam ediyor." : "Motor duraklatıldı.") }
                }
                .disabled(model.busy || !model.hasStatus)
            }
        }
        .padding(16)
        .frame(width: 520, height: 620)
        .confirmationDialog("Uygun bulunan yeniden üretilebilir çıktılar temizlensin mi?", isPresented: $confirmCleanup) {
            Button("Temizle", role: .destructive) {
                Task {
                    await model.run(["cleanup", "apply"], success: "Temizlik motoru işlemi tamamladı.")
                    cleanupPlan = nil
                }
            }
        } message: { Text("Motor uygulama öncesi koşulları yeniden doğrular. Gerçek kazanılan alan durum ekranında ayrıca görünür.") }
        .confirmationDialog("Uygulama paket planı uygulansın mı?", isPresented: $confirmApps) {
            Button("Planı uygula", role: .destructive) {
                Task {
                    await model.run(["apps", "apply"], success: "Uygulama paket planı işlendi.")
                    appPlan = nil
                }
            }
        } message: { Text("Yalnız motorun güvenli bulduğu bütün uygulama paketleri işlenir.") }
    }

    private var overview: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(spacing: 16) {
                metric("Temizlik adayı", model.summary["ready_cleanup_bytes"] is NSNumber ?
                       Display.bytes(model.summary["ready_cleanup_bytes"]) : "Önizleme gerekli")
                metric("İnceleme", Display.bytes(model.summary["review_bytes"]))
                metric("Ölçülen alan artışı", Display.bytes(model.summary["freed_bytes"]))
            }
            HStack(spacing: 16) {
                metric("Bekleyen", Display.text(model.summary, "pending_count", fallback: "0"))
                metric("Arşivlenen", Display.text(model.summary, "archived_count", fallback: "0"))
                metric("Worker", Display.text(model.status["worker"] as? [String: Any] ?? [:], "state"))
            }
            Text("Katalog bağlantısı bekleyen: \(Display.text(model.summary, "catalog_pending_count", fallback: "0"))")
                .font(.caption).foregroundStyle(.secondary)
            if model.summary["next_cleanup_at"] is String {
                Text("Sıradaki uygun temizlik: \(Display.date(model.summary["next_cleanup_at"]))")
                    .font(.caption).foregroundStyle(.secondary)
            }
            heading("Diskler ve bağlantılar")
            if model.disks.isEmpty { empty("Henüz disk durumu bildirilmedi.") }
            ForEach(model.disks.indices, id: \.self) { index in
                let disk = model.disks[index]
                VStack(alignment: .leading, spacing: 3) {
                    HStack {
                        Text(Display.text(disk, "name")).fontWeight(.medium)
                        Spacer()
                        Label(disk["available"] as? Bool == true ? "Bağlı" : "Çevrimdışı",
                              systemImage: disk["available"] as? Bool == true ? "checkmark.circle" : "wifi.slash")
                            .font(.caption)
                    }
                    Text("Boş: \(Display.bytes(disk["free_bytes"])) / \(Display.bytes(disk["total_bytes"])) · \(Display.text(disk, "location"))")
                        .font(.caption).foregroundStyle(.secondary)
                    Text("Kontrol: \(Display.date(disk["last_checked"]))")
                        .font(.caption2).foregroundStyle(.secondary)
                }
                .padding(.vertical, 4)
            }
            let worker = model.status["worker"] as? [String: Any] ?? [:]
            if let lastError = worker["last_error"] as? String, !lastError.isEmpty {
                Label(lastError, systemImage: "exclamationmark.triangle").font(.caption).foregroundStyle(.orange)
            }
            heading("Son işlemler")
            if model.recent.isEmpty { empty("Henüz işlem kaydı yok.") }
            ForEach(0..<min(model.recent.count, 5), id: \.self) { index in
                let event = model.recent[index]
                HStack(alignment: .top) {
                    Text(Display.date(event["time"]))
                        .foregroundStyle(.secondary).frame(width: 115, alignment: .leading)
                    Text(Display.text(event, "message", fallback: Display.text(event, "action")))
                }.font(.caption)
            }
        }
    }

    private var cleanup: some View {
        VStack(alignment: .leading, spacing: 10) {
            heading("Yeniden üretilebilir çıktılar")
            Text("Hazır aday: \(model.summary["ready_cleanup_bytes"] is NSNumber ? Display.bytes(model.summary["ready_cleanup_bytes"]) : "Önizleme gerekli") · İnceleme: \(Display.bytes(model.summary["review_bytes"]))")
                .font(.callout)
            HStack {
                Button("Önizlemeyi hesapla") {
                    Task { cleanupPlan = await model.query(["cleanup", "preview"]) }
                }.disabled(model.busy)
                if cleanupPlan != nil {
                    Button("Uygunları temizle") { confirmCleanup = true }
                        .disabled(model.busy || eligibleCleanup.isEmpty)
                }
            }
            if let plan = cleanupPlan {
                Text("Aday ayak izi: \(Display.bytes(plan["candidate_bytes"]))")
                    .font(.caption).foregroundStyle(.secondary)
                let candidates = plan["candidates"] as? [[String: Any]] ?? []
                if candidates.isEmpty { empty("Bu önizlemede aday yok.") }
                ForEach(candidates.indices, id: \.self) { index in
                    let item = candidates[index]
                    VStack(alignment: .leading, spacing: 3) {
                        HStack {
                            Text(Display.text(item, "path")).lineLimit(2)
                            Spacer()
                            Text(Display.bytes(item["bytes"]))
                        }
                        Text(item["eligible"] as? Bool == true ? "Uygun" : "Korunuyor: \(Display.text(item, "reason"))")
                            .font(.caption).foregroundStyle(item["eligible"] as? Bool == true ? Color.green : Color.secondary)
                    }.padding(.vertical, 4)
                }
            } else { empty("İşleme geçmeden önce güncel önizlemeyi açın.") }
        }
    }

    private var eligibleCleanup: [[String: Any]] {
        (cleanupPlan?["candidates"] as? [[String: Any]] ?? []).filter { $0["eligible"] as? Bool == true }
    }

    private var inbox: some View {
        VStack(alignment: .leading, spacing: 10) {
            heading("Gelenler kuyruğu")
            Text(Display.text(model.config, "intake_dir"))
                .font(.caption).foregroundStyle(.secondary).textSelection(.enabled)
            if model.queue.isEmpty { empty("Bekleyen veya arşivlenmiş öğe yok.") }
            ForEach(model.queue.indices, id: \.self) { index in
                let item = model.queue[index]
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(Display.text(item, "name")).fontWeight(.medium).lineLimit(2)
                        Spacer()
                        Text(Display.bytes(item["bytes"]))
                    }
                    Text("\(queueStateLabel(Display.text(item, "state"))) · \(categoryLabel(Display.text(item, "category")))")
                        .font(.caption).foregroundStyle(.secondary)
                    if let catalog = item["catalog_sync"] as? [String: Any] {
                        Text(catalogLabel(catalog))
                            .font(.caption).foregroundStyle(catalog["state"] as? String == "linked" ? Color.secondary : Color.orange)
                        if let catalogError = catalog["error"] as? String, !catalogError.isEmpty {
                            Text("Katalog: \(catalogError)").font(.caption2).foregroundStyle(.orange)
                        }
                    }
                    if let suggestion = item["suggestion"] as? String, !suggestion.isEmpty {
                        Text("Jev önerisi: \(suggestion)").font(.caption).foregroundStyle(.secondary)
                    }
                    if let error = item["error"] as? String, !error.isEmpty {
                        Text(error).font(.caption).foregroundStyle(.orange)
                    }
                    HStack {
                        let id = Display.text(item, "id", fallback: "")
                        Button("Yeniden dene") { Task { await model.run(["inbox", "retry", id]) } }
                            .disabled(id.isEmpty || model.busy)
                        Menu("Sınıf") {
                            ForEach(["ordinary", "critical", "downloadable", "review"], id: \.self) { category in
                                Button(categoryLabel(category)) { Task { await model.run(["inbox", "classify", id, "--category", category]) } }
                            }
                        }.disabled(id.isEmpty || model.busy)
                        if let path = existingLocalPath(item) {
                            Button("Aç") { openLocal(path) }
                            Button("Finder'da göster") { reveal(path) }
                        } else if canRetrieve(item) {
                            if model.retrievingIDs.contains(id) { ProgressView().controlSize(.small) }
                            Button("Aç") {
                                Task {
                                    if let url = await model.retrieve(id) { NSWorkspace.shared.open(url) }
                                }
                            }.disabled(id.isEmpty || model.retrievingIDs.contains(id))
                        }
                    }.font(.caption)
                }
                .padding(.vertical, 5)
                Divider()
            }
        }
    }

    private var workspaces: some View {
        VStack(alignment: .leading, spacing: 10) {
            heading("Kayıtlı çalışma alanları")
            if model.workspaces.isEmpty { empty("Henüz kayıtlı çalışma alanı yok.") }
            ForEach(model.workspaces.indices, id: \.self) { index in
                let item = model.workspaces[index]
                VStack(alignment: .leading, spacing: 4) {
                    HStack {
                        Text(Display.text(item, "name", fallback: Display.text(item, "path"))).fontWeight(.medium)
                        Spacer()
                        Text(Display.text(item, "state")).font(.caption)
                    }
                    Text("Sahip: \(Display.text(item, "owner")) · \(Display.text(item, "path"))")
                        .font(.caption).foregroundStyle(.secondary).lineLimit(2)
                    HStack {
                        let id = Display.text(item, "id", fallback: "")
                        let held = (item["hold"] as? Bool == true)
                        Button(held ? "Sabitlemeyi kaldır" : "Sabitle") {
                            Task { await model.run(["workspace", held ? "unpin" : "pin", id]) }
                        }.disabled(id.isEmpty || model.busy)
                        if Display.text(item, "state") != "closed" {
                            Button("Kabul edip kapat") {
                                Task { await model.run(["workspace", "close", id, "--accepted"]) }
                            }.disabled(id.isEmpty || model.busy)
                        }
                    }.font(.caption)
                }
                .padding(.vertical, 5)
                Divider()
            }
        }
    }

    private var applications: some View {
        VStack(alignment: .leading, spacing: 10) {
            heading("Uygulama paketleri")
            if displayedApplications.isEmpty { empty("Uygulama envanteri henüz yok.") }
            ForEach(displayedApplications.indices, id: \.self) { index in
                let item = displayedApplications[index]
                VStack(alignment: .leading, spacing: 3) {
                    HStack {
                        Text(Display.text(item, "name")).fontWeight(.medium)
                        Spacer()
                        Text(item["is_canonical"] as? Bool == true ? "Canonical" : "Diğer")
                            .font(.caption).foregroundStyle(.secondary)
                    }
                    Text("\(Display.text(item, "version")) · \(Display.text(item, "path"))")
                        .font(.caption).foregroundStyle(.secondary).lineLimit(2)
                    Text("Kullanım: \(appActivityLabel(item))")
                        .font(.caption).foregroundStyle(.secondary)
                    if item["is_canonical"] as? Bool != true, item["rollback"] as? Bool != true {
                        let path = Display.text(item, "path", fallback: "")
                        Button(retiredPaths.contains(path) ? "Adaylıktan çıkar" : "Eski paket adayı yap") {
                            toggleRetired(path)
                        }
                        .font(.caption)
                        .disabled(path.isEmpty || model.busy)
                    }
                }.padding(.vertical, 4)
            }
            HStack {
                Button("Paket planını önizle") { Task { appPlan = await model.query(["apps", "preview"]) } }
                    .disabled(model.busy)
                if appPlan != nil {
                    Button("Planı uygula") { confirmApps = true }
                        .disabled(model.busy || eligibleApps.isEmpty)
                }
            }
            if let plan = appPlan {
                let rows = plan["plans"] as? [[String: Any]] ?? []
                if rows.isEmpty { empty("Uygulanacak paket planı yok.") }
                ForEach(rows.indices, id: \.self) { index in
                    let row = rows[index]
                    VStack(alignment: .leading) {
                        Text(Display.text(row, "path"))
                        Text(row["eligible"] as? Bool == true ? "Uygun · \(Display.bytes(row["bytes"]))" :
                             "Korunuyor: \(Display.text(row, "reason"))")
                            .foregroundStyle(.secondary)
                    }.font(.caption).fixedSize(horizontal: false, vertical: true)
                }
            }
        }
    }

    private var eligibleApps: [[String: Any]] {
        (appPlan?["plans"] as? [[String: Any]] ?? []).filter { $0["eligible"] as? Bool == true }
    }

    private var displayedApplications: [[String: Any]] {
        appPlan?["applications"] as? [[String: Any]] ?? model.applications
    }

    private func appActivityLabel(_ item: [String: Any]) -> String {
        guard let active = item["active"] as? Bool else { return "Bilinmiyor; envanter önizlemesi gerekir" }
        return active ? "Açık" : "Kapalı"
    }

    private var retiredPaths: [String] { model.config["retired_app_paths"] as? [String] ?? [] }

    private func toggleRetired(_ path: String) {
        var paths = retiredPaths
        if paths.contains(path) { paths.removeAll { $0 == path } }
        else { paths.append(path) }
        appPlan = nil
        Task { await model.run(["config", "set"], input: ["retired_app_paths": paths], success: "Paket adayları güncellendi.") }
    }

    private func heading(_ title: String) -> some View { Text(title).font(.subheadline.weight(.semibold)) }
    private func categoryLabel(_ category: String) -> String {
        switch category {
        case "ordinary": return "Olağan"
        case "critical": return "Kritik"
        case "downloadable": return "Yeniden indirilebilir"
        case "review": return "İnceleme"
        default: return "Sınıflandırılmadı"
        }
    }
    private func queueStateLabel(_ state: String) -> String {
        switch state {
        case "pending": return "İşlem bekliyor"
        case "settling": return "Dosya tamamlanması bekleniyor"
        case "in_use": return "Kullanımda; kaynak korunuyor"
        case "review": return "Karar bekliyor"
        case "waiting_download": return "İndirme tamamlanması bekleniyor"
        case "transferring": return "Aktarılıyor"
        case "verifying": return "Doğrulanıyor"
        case "catalog_pending": return "Katalog bağlantısı bekleniyor; kaynak korunuyor"
        case "archived": return "Arşivlendi"
        case "grace": return "Arşivlendi; yerel bekleme sürüyor"
        case "second_copy_required": return "İkinci kopya bekleniyor"
        case "evicting": return "Yerel kaynak kaldırılıyor"
        case "review_claim": return "Kaynak çakışması incelemede"
        case "evicted": return "Arşivlendi; Pro kaynağı kaldırıldı"
        case "missing": return "Kaynak bulunamadı"
        case "error": return "İşlem hatası"
        default: return state
        }
    }
    private func catalogLabel(_ catalog: [String: Any]) -> String {
        switch Display.text(catalog, "state") {
        case "linked": return "Katalog bağlı · \(Display.text(catalog, "snapshot_id"))"
        case "gap": return "Katalog bağlantısı eksik"
        case "not_configured": return "Katalog bağlantısı yapılandırılmadı"
        default: return "Katalog durumu bilinmiyor"
        }
    }
    private func canRetrieve(_ item: [String: Any]) -> Bool {
        guard item["archive_path"] is String else { return false }
        return ["archived", "grace", "evicted", "catalog_pending", "second_copy_required"]
            .contains(Display.text(item, "state"))
    }
    private func empty(_ title: String) -> some View { Text(title).font(.callout).foregroundStyle(.secondary).padding(.vertical, 4) }
    private func metric(_ title: String, _ value: String) -> some View {
        VStack(alignment: .leading, spacing: 3) {
            Text(title).font(.caption).foregroundStyle(.secondary)
            Text(value).font(.title3.weight(.semibold)).lineLimit(1).minimumScaleFactor(0.75)
        }.frame(maxWidth: .infinity, alignment: .leading)
    }
    private func openLocal(_ path: String) {
        let url = URL(fileURLWithPath: path)
        guard url.isFileURL, FileManager.default.fileExists(atPath: url.path) else { return }
        NSWorkspace.shared.open(url)
    }
    private func existingLocalPath(_ item: [String: Any]) -> String? {
        guard let path = item["local_path"] as? String, path.hasPrefix("/"),
              FileManager.default.fileExists(atPath: path) else { return nil }
        return path
    }
    private func reveal(_ path: String) {
        let url = URL(fileURLWithPath: path)
        guard url.isFileURL, FileManager.default.fileExists(atPath: url.path) else { return }
        NSWorkspace.shared.activateFileViewerSelecting([url])
    }
}
