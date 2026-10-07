import AppKit
import Foundation
import Security
import ServiceManagement
import SwiftUI

private struct EngineFailure: LocalizedError {
    let message: String
    var errorDescription: String? { message }
}

private enum StorageEngine {
    static func call(configPath: String, arguments: [String], input: [String: Any]? = nil) async throws -> [String: Any] {
        try await withCheckedThrowingContinuation { continuation in
            DispatchQueue.global(qos: .utility).async {
                do {
                    let home = FileManager.default.homeDirectoryForCurrentUser
                    let launcher = home.appendingPathComponent(".local/bin/skillry-storage")
                    let bundled = Bundle.main.resourceURL?.appendingPathComponent("engine/storage.py")
                    let process = Process()
                    var environment = ProcessInfo.processInfo.environment
                    environment["PYTHONDONTWRITEBYTECODE"] = "1"
                    process.environment = environment
                    if FileManager.default.isExecutableFile(atPath: launcher.path) {
                        process.executableURL = launcher
                        process.arguments = ["--config", configPath] + arguments
                    } else if let bundled, FileManager.default.fileExists(atPath: bundled.path) {
                        process.executableURL = URL(fileURLWithPath: "/usr/bin/env")
                        process.arguments = ["python3", "-B", bundled.path, "--config", configPath] + arguments
                    } else {
                        throw EngineFailure(message: "Skillry Storage motoru bulunamadı. Yardımcı uygulamayı kurun veya yerel başlatıcıyı bağlayın.")
                    }
                    let output = Pipe()
                    process.standardOutput = output
                    process.standardError = FileHandle.nullDevice
                    if let input {
                        let pipe = Pipe()
                        process.standardInput = pipe
                        try process.run()
                        let data = try JSONSerialization.data(withJSONObject: input)
                        pipe.fileHandleForWriting.write(data)
                        pipe.fileHandleForWriting.closeFile()
                    } else {
                        process.standardInput = FileHandle.nullDevice
                        try process.run()
                    }
                    let probeTimeout: TimeInterval? = arguments == ["status"] ? 60 :
                        arguments == ["config", "read"] ? 30 : nil
                    if let probeTimeout {
                        DispatchQueue.global(qos: .utility).asyncAfter(deadline: .now() + probeTimeout) {
                            if process.isRunning { process.terminate() }
                        }
                    }
                    let data = output.fileHandleForReading.readDataToEndOfFile()
                    process.waitUntilExit()
                    guard let object = try JSONSerialization.jsonObject(with: data) as? [String: Any] else {
                        throw EngineFailure(message: "Motordan geçerli JSON yanıtı alınamadı (çıkış: \(process.terminationStatus)).")
                    }
                    guard object["schema_version"] as? Int == 1 else {
                        throw EngineFailure(message: "Motorun yanıt sürümü bu uygulamayla uyumlu değil.")
                    }
                    guard object["ok"] as? Bool == true, process.terminationStatus == 0 else {
                        let raw = object["error"]
                        let detail = (raw as? [String: Any])?["message"] as? String ?? raw as? String ?? "İşlem tamamlanamadı."
                        throw EngineFailure(message: detail)
                    }
                    continuation.resume(returning: object)
                } catch {
                    continuation.resume(throwing: error)
                }
            }
        }
    }
}

@MainActor
final class StorageModel: ObservableObject {
    @Published private(set) var status: [String: Any] = [:]
    @Published private(set) var loading = false
    @Published private(set) var busy = false
    @Published private(set) var message: String?
    @Published private(set) var errorMessage: String?
    @Published private(set) var lastUpdated: Date?
    @Published private(set) var retrievingIDs: Set<String> = []
    @Published private(set) var loginStatus = SMAppService.mainApp.status
    @Published var configPath: String {
        didSet { UserDefaults.standard.set(configPath, forKey: "storageConfigPath") }
    }

    private var timer: Timer?
    private var ticking = false

    init() {
        configPath = UserDefaults.standard.string(forKey: "storageConfigPath")
            ?? FileManager.default.homeDirectoryForCurrentUser.appendingPathComponent(".config/skillry/storage.json").path
        timer = Timer.scheduledTimer(withTimeInterval: 60, repeats: true) { [weak self] _ in
            Task { @MainActor in await self?.tick() }
        }
        if CommandLine.arguments.contains("--enable-login") { enableLoginFromLaunch() }
        Task { await refresh() }
    }

    var paused: Bool { status["paused"] as? Bool ?? false }
    var hasStatus: Bool { !status.isEmpty }
    var summary: [String: Any] { status["summary"] as? [String: Any] ?? [:] }
    var config: [String: Any] { status["config"] as? [String: Any] ?? [:] }
    var jev: [String: Any] { status["jev"] as? [String: Any] ?? [:] }
    var disks: [[String: Any]] { status["disks"] as? [[String: Any]] ?? [] }
    var workspaces: [[String: Any]] { status["workspaces"] as? [[String: Any]] ?? [] }
    var queue: [[String: Any]] { status["queue"] as? [[String: Any]] ?? [] }
    var applications: [[String: Any]] { status["applications"] as? [[String: Any]] ?? [] }
    var tools: [[String: Any]] { status["tools"] as? [[String: Any]] ?? [] }
    var recent: [[String: Any]] { status["recent"] as? [[String: Any]] ?? [] }

    func refresh() async {
        if busy { return }
        loading = true
        defer { loading = false }
        do {
            status = try await StorageEngine.call(configPath: configPath, arguments: ["status"])
            lastUpdated = Date()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func tick() async {
        guard !ticking, !busy else { return }
        ticking = true
        defer { ticking = false }
        do {
            _ = try await StorageEngine.call(configPath: configPath, arguments: ["tick"])
            status = try await StorageEngine.call(configPath: configPath, arguments: ["status"])
            lastUpdated = Date()
            errorMessage = nil
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func run(_ arguments: [String], input: [String: Any]? = nil, success: String? = nil) async {
        guard !busy, !ticking || arguments.first == "pause" else { return }
        busy = true
        message = nil
        errorMessage = nil
        defer { busy = false }
        do {
            _ = try await StorageEngine.call(configPath: configPath, arguments: arguments, input: input)
            let newStatus = try await StorageEngine.call(configPath: configPath, arguments: ["status"])
            if arguments.first == "pause", newStatus["paused"] as? Bool != true {
                throw EngineFailure(message: "Motor durdurma onayı vermedi.")
            }
            if arguments.first == "resume", newStatus["paused"] as? Bool != false {
                throw EngineFailure(message: "Motor devam onayı vermedi.")
            }
            status = newStatus
            lastUpdated = Date()
            message = success
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func query(_ arguments: [String]) async -> [String: Any]? {
        guard !busy else { return nil }
        busy = true
        errorMessage = nil
        defer { busy = false }
        do { return try await StorageEngine.call(configPath: configPath, arguments: arguments) }
        catch {
            errorMessage = error.localizedDescription
            return nil
        }
    }

    func retrieve(_ id: String) async -> URL? {
        guard !id.isEmpty, !retrievingIDs.contains(id) else { return nil }
        retrievingIDs.insert(id)
        errorMessage = nil
        defer { retrievingIDs.remove(id) }
        do {
            let response = try await StorageEngine.call(configPath: configPath,
                                                        arguments: ["inbox", "retrieve", "--id", id])
            guard let retrieval = response["retrieval"] as? [String: Any],
                  let path = retrieval["path"] as? String, path.hasPrefix("/"),
                  FileManager.default.fileExists(atPath: path) else {
                throw EngineFailure(message: "Doğrulanmış yerel kopya alınamadı.")
            }
            return URL(fileURLWithPath: path)
        } catch {
            errorMessage = error.localizedDescription
            return nil
        }
    }

    func switchConfig(to path: String) async {
        configPath = path
        status = [:]
        lastUpdated = nil
        await refresh()
    }

    func saveJevKey(_ secret: String) async {
        guard !secret.isEmpty else { return }
        let reference = jev
        let service = reference["service"] as? String ?? "skillry.typesafe"
        let account = reference["account"] as? String ?? NSUserName()
        busy = true
        defer { busy = false }
        do {
            try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
                DispatchQueue.global(qos: .utility).async {
                    let query: [String: Any] = [kSecClass as String: kSecClassGenericPassword,
                                                kSecAttrService as String: service,
                                                kSecAttrAccount as String: account]
                    let value = Data(secret.utf8)
                    var status = SecItemUpdate(query as CFDictionary, [kSecValueData as String: value] as CFDictionary)
                    if status == errSecItemNotFound {
                        var item = query
                        item[kSecValueData as String] = value
                        status = SecItemAdd(item as CFDictionary, nil)
                    }
                    if status == errSecSuccess {
                        continuation.resume()
                    } else {
                        continuation.resume(throwing: EngineFailure(message: "Anahtar Keychain'e kaydedilemedi (\(status)). macOS erişim iznini kontrol edin."))
                    }
                }
            }
            _ = try await StorageEngine.call(configPath: configPath, arguments: ["config", "set"],
                                             input: ["jev": ["secret_kind": "keychain", "service": service, "account": account]])
            message = "Jev anahtarı Keychain'e kaydedildi ve motor bağlantısı ayarlandı."
            errorMessage = nil
            status = try await StorageEngine.call(configPath: configPath, arguments: ["status"])
            lastUpdated = Date()
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func setLaunchAtLogin(_ enabled: Bool) {
        refreshLoginStatus()
        do {
            if loginStatus == .notFound {
                throw EngineFailure(message: "macOS bu uygulamanın oturum açılış kaydını bulamadı. Yüklü uygulamayı açın.")
            }
            if enabled {
                if loginStatus == .notRegistered { try SMAppService.mainApp.register() }
            } else if loginStatus == .enabled || loginStatus == .requiresApproval {
                try SMAppService.mainApp.unregister()
            }
            refreshLoginStatus()
            message = loginStatus == .enabled ? "Oturum açılışında başlatma etkin." :
                loginStatus == .requiresApproval ? "Oturum açılışında başlatma macOS onayını bekliyor." :
                "Oturum açılışında başlatma kapalı."
            errorMessage = nil
        } catch {
            refreshLoginStatus()
            errorMessage = "Oturum açılış ayarı değiştirilemedi: \(error.localizedDescription)"
        }
    }

    private func enableLoginFromLaunch() {
        refreshLoginStatus()
        if loginStatus == .notFound {
            errorMessage = "macOS bu uygulamanın oturum açılış kaydını bulamadı. Yüklü uygulamayı açın."
            return
        }
        guard loginStatus == .notRegistered else { return }
        setLaunchAtLogin(true)
    }

    func refreshLoginStatus() { loginStatus = SMAppService.mainApp.status }

    var launchAtLogin: Bool { loginStatus == .enabled }
    var loginStatusText: String {
        switch loginStatus {
        case .enabled: return "Etkin"
        case .requiresApproval: return "macOS onayı gerekiyor"
        case .notRegistered: return "Kapalı"
        case .notFound: return "Uygulama bulunamadı"
        @unknown default: return "Bilinmiyor"
        }
    }
}

enum Display {
    static func text(_ object: [String: Any], _ key: String, fallback: String = "—") -> String {
        if let text = object[key] as? String, !text.isEmpty { return text }
        if let number = object[key] as? NSNumber { return number.stringValue }
        return fallback
    }

    static func bytes(_ value: Any?) -> String {
        guard let number = value as? NSNumber else { return "—" }
        return ByteCountFormatter.string(fromByteCount: number.int64Value, countStyle: .file)
    }

    static func date(_ value: Any?) -> String {
        if let number = value as? NSNumber {
            return Date(timeIntervalSince1970: number.doubleValue).formatted(date: .abbreviated, time: .shortened)
        }
        guard let text = value as? String, let date = ISO8601DateFormatter().date(from: text) else {
            return value as? String ?? "—"
        }
        return date.formatted(date: .abbreviated, time: .shortened)
    }
}
