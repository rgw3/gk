//
//  ContentView.swift
//  GoalKick
//
//  Tab bar container, and the landing point for clips sent to the app from
//  outside it.
//

import SwiftUI

struct ContentView: View {

    private enum Tab: Hashable {
        case record, review
        case ane          // TEMPORARY — punch list 1.1, remove with ANEComparison.swift
    }

    @State private var selection: Tab = .record
    @State private var importTitle = ""
    @State private var importMessage = ""
    @State private var showingImportResult = false

    var body: some View {
        TabView(selection: $selection) {
            RecordView()
                .tabItem {
                    Label("Record", systemImage: "video.fill")
                }
                .tag(Tab.record)

            ReviewView()
                .tabItem {
                    Label("Review", systemImage: "play.rectangle.fill")
                }
                .tag(Tab.review)

            // TEMPORARY — punch list item 1.1. Delete this tab and
            // ANEComparison.swift once the Neural Engine question is settled.
            ANEComparisonView()
                .tabItem {
                    Label("ANE", systemImage: "cpu")
                }
                .tag(Tab.ane)
        }
        // Fires when a clip is AirDropped to GoalKick, or opened into it from
        // the Files app. Without the CFBundleDocumentTypes declaration in
        // Info.plist the app is never offered as a destination and this never
        // runs at all.
        .onOpenURL(perform: receive)
        .alert(importTitle, isPresented: $showingImportResult) {
            Button("OK", role: .cancel) { }
        } message: {
            Text(importMessage)
        }
    }

    /// Copies an incoming clip into the app's library and says what happened.
    ///
    /// The result is reported either way. A silent failure here would look
    /// exactly like a successful transfer until the coach went looking for a
    /// clip that was never there.
    private func receive(_ url: URL) {
        do {
            let imported = try ClipStore.importClip(from: url)
            selection = .review
            importTitle = "Clip added"
            importMessage = "\(imported.lastPathComponent) is in your clips. "
                + "Tap Choose clip to open it."
        } catch {
            importTitle = "Could not add clip"
            importMessage = error.localizedDescription
        }
        showingImportResult = true
    }
}

#Preview {
    ContentView()
}
