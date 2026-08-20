//
//  ContentView.swift
//  GoalKick
//
//  Created by Rocket Williams on 8/20/26.
//

import SwiftUI

struct ContentView: View {
    var body: some View {
        TabView {
            RecordView()
                .tabItem {
                    Label("Record", systemImage: "video.fill")
                }

            ReviewView()
                .tabItem {
                    Label("Review", systemImage: "play.rectangle.fill")
                }
        }
    }
}

#Preview {
    ContentView()
}
