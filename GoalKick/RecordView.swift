//
//  RecordView.swift
//  GoalKick
//
//  The capture screen: live preview, configuration picker, record button.
//

import SwiftUI

struct RecordView: View {

    @StateObject private var recorder = Recorder()

    var body: some View {
        ZStack {
            CameraPreview(recorder: recorder)
                .ignoresSafeArea()

            VStack {
                configPicker

                statusPanel

                Spacer()

                recordButton
                    .padding(.bottom, 30)
            }
            .padding()
        }
        .onAppear {
            recorder.start()
        }
    }

    private var configPicker: some View {
        Picker("Capture configuration", selection: Binding(
            get: { recorder.config },
            set: { recorder.select($0) }
        )) {
            ForEach(CaptureConfig.allCases) { config in
                Text(config.rawValue).tag(config)
            }
        }
        .pickerStyle(.segmented)
        .disabled(recorder.isRecording || !recorder.isReady)
    }

    private var statusPanel: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(recorder.status)
                .font(.system(.footnote, design: .monospaced))
                .foregroundStyle(.white)
            if !recorder.detail.isEmpty {
                Text(recorder.detail)
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundStyle(.white.opacity(0.75))
            }
            if !recorder.verification.isEmpty {
                Text(recorder.verification)
                    .font(.system(.caption2, design: .monospaced))
                    .foregroundStyle(.green)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(10)
        .background(.black.opacity(0.6), in: RoundedRectangle(cornerRadius: 10))
    }

    private var recordButton: some View {
        Button {
            recorder.toggleRecording()
        } label: {
            ZStack {
                Circle()
                    .stroke(.white, lineWidth: 4)
                    .frame(width: 78, height: 78)

                RoundedRectangle(cornerRadius: recorder.isRecording ? 6 : 32)
                    .fill(.red)
                    .frame(width: recorder.isRecording ? 32 : 64,
                           height: recorder.isRecording ? 32 : 64)
            }
        }
        .disabled(!recorder.isReady)
        .animation(.easeInOut(duration: 0.2), value: recorder.isRecording)
    }
}

#Preview {
    RecordView()
}
