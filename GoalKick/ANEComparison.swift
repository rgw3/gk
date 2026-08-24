//
//  ANEComparison.swift
//  GoalKick
//
//  TEMPORARY HARNESS — punch list item 1.1. Delete this file, and the three
//  lines it adds to ContentView.swift, once the question below is answered.
//
//  THE QUESTION
//
//  yolo11n.mlpackage reproduces the PyTorch bounding boxes to 0.00%, but that
//  was measured with Ultralytics driving Core ML on the Mac's CPU or GPU. The
//  Neural Engine is a different compute unit, it may run the network in
//  float16, and it is what actually executes on the phone. So the export is
//  proven as a *conversion* and merely assumed as a *runtime*.
//
//  THE METHOD, AND WHY IT IS NOT THE OBVIOUS ONE
//
//  The obvious test is "run it in Swift, compare against the Python numbers".
//  That is a weak test: Swift and Python differ in how they decode video,
//  resize, and order colour channels, so any discrepancy would be ambiguous
//  between the runtime and the plumbing.
//
//  Instead this runs ONE piece of code over IDENTICAL pixels FOUR times,
//  changing only MLComputeUnits. Core ML gives no way to demand the Neural
//  Engine, but .cpuOnly provably excludes it — so the difference between
//  .cpuOnly and .cpuAndNeuralEngine is the ANE effect, with nothing else
//  varying. The Mac's numbers are a third data point, not the yardstick.
//
//  The inputs are the four 640x640 crops frozen by
//
//      tools/export_coreml.py dump
//
//  and carried in the app bundle with a .pngraw extension. The extension is
//  deliberate: Xcode's COMPRESS_PNG_FILES setting rewrites bundled .png files
//  into Apple's CgBI variant at build time, and an asset catalogue may
//  re-encode them again. Either would mean the phone is not reading the bytes
//  the Mac baseline was measured from, which is the one property this whole
//  experiment rests on. Xcode has no opinion about .pngraw and copies it
//  verbatim; ImageIO decodes by sniffing content, not by extension.
//
//  MLModel is driven directly rather than through VNCoreMLRequest, because
//  Vision applies its own scaling and cropping and that is a variable which
//  does not belong inside a numerical comparison. Vision arrives at item 4.1,
//  where it is the thing under test rather than an uncontrolled input.
//
//  THE MAC BASELINE, measured 2026-08-24 (see project_notes.md item 1.1):
//
//      crop   true diameter   PyTorch and Core ML (Mac CPU/GPU)
//      f620         57.2 px   58.28 px  c0.96
//      f660         52.4 px   54.12 px  c0.94
//      f700         37.7 px   37.63 px  c0.94
//      f740         30.4 px   30.35 px  c0.35
//
//  Watch f740 in particular. Confidence there is 0.35 against the detector's
//  0.25 threshold — only 0.10 of headroom, where every other frame sits at
//  0.94 or better. If the Neural Engine moves confidences at all, that is the
//  frame where it shows up as the ball VANISHING rather than as a small
//  numeric difference, and a frame lost late in flight is exactly where the
//  diameter bias of item 3.1 lives.
//

import CoreML
import SwiftUI
import UIKit

// MARK: - Model output decoding

/// One detection: where the box is, how big, and how sure the model was.
///
/// `struct` in Swift is a *value* type — assigning it copies it, unlike a
/// Python object reference. That is what you want for a small bag of numbers.
struct BallDetection {
    let diameter: Double
    let confidence: Double
    let centreX: Double
    let centreY: Double
}

enum ANEComparison {

    /// COCO class index for "sports ball". The detector is stock yolo11n
    /// trained on COCO, so a football arrives through this class with no
    /// training data of our own — see project_notes.md, Tech Stack.
    static let sportsBall = 32

    /// COCO has 80 classes, and YOLO emits 4 box coordinates before them.
    static let classCount = 80
    static let boxCoordinateCount = 4
    static var featureRows: Int { boxCoordinateCount + classCount }   // 84

    /// The model input, fixed at export time. Also the crop size that ships.
    static let inputSize = 640

    /// Matches `--confidence` in tools/detect_ball.py, so the Swift and the
    /// Python are applying the same bar.
    static let confidenceThreshold = 0.25

    // MARK: Running one image through one configuration

    /// Runs the model once and returns the largest sports ball it found.
    ///
    /// The return type is `BallDetection?` — an *optional*. Swift has no
    /// implicit null: a value either exists or the type says it might not,
    /// and the compiler forces the caller to deal with the second case. It is
    /// `nil` here when the model found no ball above the threshold, which is
    /// a real outcome worth reporting rather than an error.
    ///
    /// `throws` means this can fail in a way the caller must handle, with
    /// `try`. Loading a model and running inference can both genuinely fail.
    static func detect(in pixels: CVPixelBuffer, using model: MLModel)
        throws -> (largest: BallDetection?,
                   mostConfident: BallDetection?,
                   shape: String) {

        // The input feature is called "image" in this export, but read the
        // name from the model rather than hardcoding it — an export with a
        // different name would otherwise fail at runtime with a message that
        // does not obviously say why.
        guard let inputName = model.modelDescription
            .inputDescriptionsByName.keys.first else {
            throw HarnessError.message("Model declares no inputs.")
        }

        let input = try MLDictionaryFeatureProvider(
            dictionary: [inputName: MLFeatureValue(pixelBuffer: pixels)])

        let output = try model.prediction(from: input)

        // The model was exported with nms=False, deliberately: detect_ball.py
        // does its own candidate selection — nearest ball wins, gated on the
        // paced camera distance — and baked-in NMS would discard the very
        // candidates that choice depends on. So the output is a raw tensor,
        // not tidy detections, and the decoding below is what Ultralytics
        // does for us on the Mac.
        guard let outputName = output.featureNames.first,
              let array = output.featureValue(for: outputName)?.multiArrayValue else {
            throw HarnessError.message("Model produced no multi-array output.")
        }

        // The element type is reported because it is itself evidence. If a
        // configuration hands back float16 where another gave float32, that
        // is the Neural Engine's precision showing up directly rather than
        // being inferred from a difference in the numbers.
        let shape = array.shape.map { $0.intValue }
        let typeName: String
        switch array.dataType {
        case .float32: typeName = "float32"
        case .float16: typeName = "float16"
        case .double: typeName = "float64"
        case .int32: typeName = "int32"
        @unknown default: typeName = "unknown"
        }
        let shapeNote = "\(outputName) \(shape) \(typeName)"

        let found = bestBalls(in: array)
        return (found.largest, found.mostConfident, shapeNote)
    }

    /// Picks sports balls out of the raw output tensor, two ways.
    ///
    /// **Why two.** The Mac pipeline's acquisition rule is *largest candidate,
    /// not most confident* — the ball being measured is the one the coach
    /// stood 10 yards from, so it is the nearest object in shot and therefore
    /// the biggest. Taking the most confident instead picked a football 25 m
    /// away in nine clips out of eleven. That rule is right and is not in
    /// question.
    ///
    /// But the Mac applies it to boxes Ultralytics has already run NMS over —
    /// one box per object. This decoder applies it to the raw tensor, where
    /// many anchors fire on the same ball with slightly different boxes. So
    /// "largest" here means largest *duplicate*, which is reliably a little
    /// bigger and a little less confident than the box NMS would have kept.
    ///
    /// Measured 2026-08-24 on device, the largest-box rule read every diameter
    /// 0.46–1.36% high and every confidence 0.04–0.12 low against the Mac. If
    /// the most-confident column below matches the Mac exactly, that gap is
    /// this decoder rather than the runtime — and item 4.1 learns that the
    /// port needs NMS before the largest-candidate rule can be applied to it.
    static func bestBalls(in array: MLMultiArray)
        -> (largest: BallDetection?, mostConfident: BallDetection?) {

        let shape = array.shape.map { $0.intValue }

        // Expected [1, 84, 8400], but do not assume the ordering. Find which
        // axis carries the 84 features and treat the other as the anchors.
        // Being wrong here would silently read class scores as coordinates.
        var featureAxis = -1
        var anchorAxis = -1
        for (axis, extent) in shape.enumerated() where extent == featureRows {
            featureAxis = axis
        }
        guard featureAxis >= 0 else { return (nil, nil) }
        for (axis, extent) in shape.enumerated()
        where axis != featureAxis && extent > featureRows {
            anchorAxis = axis
        }
        guard anchorAxis >= 0 else { return (nil, nil) }

        let anchorCount = shape[anchorAxis]
        let strides = array.strides.map { $0.intValue }
        let featureStride = strides[featureAxis]
        let anchorStride = strides[anchorAxis]

        // Read the element type rather than assuming it. `withUnsafeBufferPointer`
        // traps if the type it is given does not match what the array holds,
        // and a model whose output is float16 is not hypothetical here — it is
        // one of the things the Neural Engine might do, and therefore one of
        // the things this harness exists to discover. Crashing on the finding
        // would be a poor way to learn it.
        var best: BallDetection?
        var mostConfident: BallDetection?

        /// Shared decoding, given a way to read element *i* as a Double.
        ///
        /// This is a closure taking a closure. `(Int) -> Double` is a function
        /// type: `read` is a function you can call, passed in as a value. It
        /// lets one copy of the loop serve both element types.
        func scan(_ read: (Int) -> Double) {
            for anchor in 0..<anchorCount {
                let base = anchor * anchorStride

                let score = read(base + (boxCoordinateCount + sportsBall) * featureStride)
                guard score >= confidenceThreshold else { continue }

                let x = read(base + 0 * featureStride)
                let y = read(base + 1 * featureStride)
                let w = read(base + 2 * featureStride)
                let h = read(base + 3 * featureStride)

                // Some exports emit coordinates normalised to 0...1 and some
                // in pixels. Decide from the data rather than from belief: a
                // width of 0.09 cannot be pixels, and one of 58 cannot be a
                // fraction.
                let scale = (w <= 1.5 && h <= 1.5) ? Double(inputSize) : 1.0

                let diameter = (w * scale + h * scale) / 2
                let candidate = BallDetection(diameter: diameter,
                                              confidence: score,
                                              centreX: x * scale,
                                              centreY: y * scale)
                if best == nil || diameter > best!.diameter {
                    best = candidate
                }
                if mostConfident == nil || score > mostConfident!.confidence {
                    mostConfident = candidate
                }
            }
        }

        switch array.dataType {
        case .float32:
            array.withUnsafeBufferPointer(ofType: Float.self) { buffer in
                scan { Double(buffer[$0]) }
            }
        case .float16:
            array.withUnsafeBufferPointer(ofType: Float16.self) { buffer in
                scan { Double(buffer[$0]) }
            }
        case .double:
            array.withUnsafeBufferPointer(ofType: Double.self) { buffer in
                scan { buffer[$0] }
            }
        default:
            return (nil, nil)
        }
        return (best, mostConfident)
    }

    // MARK: The comparison itself

    /// The four compute-unit configurations, in the order they are reported.
    ///
    /// `.cpuAndNeuralEngine` is the sharpest probe available: it excludes the
    /// GPU as well, so a difference from `.cpuOnly` can only be the ANE.
    /// `.all` is included because it is what production code would normally
    /// use and Core ML decides for itself what to run where.
    static let configurations: [(name: String, units: MLComputeUnits)] = [
        ("cpuOnly", .cpuOnly),
        ("cpuAndGPU", .cpuAndGPU),
        ("cpuAndANE", .cpuAndNeuralEngine),
        ("all", .all),
    ]

    /// Runs every bundled crop through every configuration and formats a report.
    static func run() -> String {

        var lines: [String] = []
        lines.append("GoalKick — punch list 1.1, Neural Engine box comparison")
        lines.append(stamp())
        lines.append(deviceDescription())
        lines.append("")

        let inputs: [URL]
        do {
            inputs = try bundledCrops()
        } catch {
            return lines.joined(separator: "\n")
                + "\n\nFAILED: \(error.localizedDescription)"
        }

        // Load each configuration once rather than per image. Compiling and
        // loading is the expensive part and it is not what is being measured.
        var models: [(name: String, model: MLModel)] = []
        for configuration in configurations {
            do {
                models.append((configuration.name,
                               try loadModel(units: configuration.units)))
            } catch {
                lines.append("\(configuration.name): could not load — \(error)")
            }
        }
        guard !models.isEmpty else {
            return lines.joined(separator: "\n") + "\n\nFAILED: no model loaded."
        }

        // Keyed by configuration, not a single value: if one compute unit
        // returns a different tensor type from another, that difference is
        // the finding and must not be overwritten by whichever ran last.
        var shapes: [String: String] = [:]
        var worstSpread = 0.0

        for input in inputs {
            lines.append(input.deletingPathExtension().lastPathComponent)

            guard let pixels = pixelBuffer(from: input) else {
                lines.append("   could not read image")
                lines.append("")
                continue
            }

            var diameters: [Double] = []
            for entry in models {
                do {
                    let result = try detect(in: pixels, using: entry.model)
                    shapes[entry.name] = result.shape

                    let name = entry.name.padding(toLength: 10,
                                                  withPad: " ", startingAt: 0)

                    // Both selection rules, side by side. "largest" is the
                    // Mac's acquisition rule applied to raw anchors; "best"
                    // is the nearest thing to what NMS would have kept.
                    let largest = result.largest.map {
                        String(format: "%7.2f px c%.4f", $0.diameter, $0.confidence)
                    } ?? "      NOT FOUND"
                    let best = result.mostConfident.map {
                        String(format: "%7.2f px c%.4f", $0.diameter, $0.confidence)
                    } ?? "      NOT FOUND"

                    lines.append("   \(name) largest \(largest)")
                    lines.append("   \(name) best    \(best)")

                    if let ball = result.largest {
                        diameters.append(ball.diameter)
                    }
                } catch {
                    lines.append("   \(entry.name): error — \(error)")
                }
            }

            // The headline number: how far apart the runtimes are on this
            // image. If this is 0.00 everywhere, the Neural Engine changes
            // nothing and every Mac-side measurement transfers intact.
            if let low = diameters.min(), let high = diameters.max(), low > 0 {
                let spread = 100 * (high / low - 1)
                worstSpread = max(worstSpread, spread)
                lines.append(String(format: "   spread %.2f%%", spread))
            }
            lines.append("")
        }

        lines.append("Output tensor, per compute unit:")
        for configuration in configurations {
            let note = shapes[configuration.name] ?? "not run"
            lines.append("   \(configuration.name): \(note)")
        }
        lines.append(String(format: "Worst spread across compute units: %.2f%%",
                            worstSpread))
        lines.append("")
        lines.append("Mac baseline, 2026-08-24, PyTorch and Core ML identical:")
        lines.append("   f620  58.28 px  c0.96   (truth 57.2)")
        lines.append("   f660  54.12 px  c0.94   (truth 52.4)")
        lines.append("   f700  37.63 px  c0.94   (truth 37.7)")
        lines.append("   f740  30.35 px  c0.35   (truth 30.4)")
        lines.append("")
        lines.append("Reading this. The spread figure is the clean result: one")
        lines.append("piece of code, identical pixels, only MLComputeUnits")
        lines.append("changed.")
        lines.append("")
        lines.append("The largest/best pair is the second question. The Mac")
        lines.append("runs NMS before applying its largest-candidate rule;")
        lines.append("this decoder has no NMS, so 'largest' means largest")
        lines.append("duplicate anchor. If 'best' matches the Mac column and")
        lines.append("'largest' does not, the device-vs-Mac gap is selection")
        lines.append("rather than arithmetic — the runtime is vindicated, and")
        lines.append("item 4.1 needs NMS before the largest-candidate rule")
        lines.append("can be applied on device.")

        return lines.joined(separator: "\n")
    }

    // MARK: Loading

    static func loadModel(units: MLComputeUnits) throws -> MLModel {
        // Xcode compiles yolo11n.mlpackage into yolo11n.mlmodelc at build
        // time, so it is the compiled form that is in the bundle.
        guard let url = Bundle.main.url(forResource: "yolo11n",
                                        withExtension: "mlmodelc") else {
            throw HarnessError.message(
                "yolo11n.mlmodelc not in the bundle. Is yolo11n.mlpackage "
                + "inside GoalKick/ ?")
        }
        let configuration = MLModelConfiguration()
        configuration.computeUnits = units
        return try MLModel(contentsOf: url, configuration: configuration)
    }

    /// The frozen crops, sorted so the report order is stable between runs.
    static func bundledCrops() throws -> [URL] {
        let urls = Bundle.main.urls(forResourcesWithExtension: "pngraw",
                                    subdirectory: nil) ?? []
        guard !urls.isEmpty else {
            throw HarnessError.message(
                "No .pngraw crops in the bundle. Run tools/export_coreml.py "
                + "dump, then copy the crops into GoalKick/.")
        }
        return urls.sorted { $0.lastPathComponent < $1.lastPathComponent }
    }

    /// Decodes one crop into the 640x640 buffer Core ML wants.
    ///
    /// Colour order is the trap here. OpenCV wrote the PNG from BGR data, so
    /// the file itself has correct colour; UIImage decodes it to RGB, and
    /// drawing into a 32BGRA buffer gives Core ML what its image input
    /// expects. Handing Swift a raw BGR buffer instead would swap red and
    /// blue and quietly change every box.
    static func pixelBuffer(from url: URL) -> CVPixelBuffer? {
        guard let data = try? Data(contentsOf: url),
              let image = UIImage(data: data),
              let cgImage = image.cgImage else { return nil }

        let attributes: [CFString: Any] = [
            kCVPixelBufferCGImageCompatibilityKey: true,
            kCVPixelBufferCGBitmapContextCompatibilityKey: true,
        ]

        var buffer: CVPixelBuffer?
        let status = CVPixelBufferCreate(kCFAllocatorDefault,
                                         inputSize, inputSize,
                                         kCVPixelFormatType_32BGRA,
                                         attributes as CFDictionary,
                                         &buffer)
        guard status == kCVReturnSuccess, let pixels = buffer else { return nil }

        CVPixelBufferLockBaseAddress(pixels, [])
        defer { CVPixelBufferUnlockBaseAddress(pixels, []) }

        guard let context = CGContext(
            data: CVPixelBufferGetBaseAddress(pixels),
            width: inputSize,
            height: inputSize,
            bitsPerComponent: 8,
            bytesPerRow: CVPixelBufferGetBytesPerRow(pixels),
            space: CGColorSpaceCreateDeviceRGB(),
            bitmapInfo: CGImageAlphaInfo.noneSkipFirst.rawValue
                | CGBitmapInfo.byteOrder32Little.rawValue
        ) else { return nil }

        // The crops are already exactly 640x640, so this is a straight copy
        // and not a resample. If it ever is not, that is a bug worth seeing
        // rather than silently absorbing.
        context.draw(cgImage,
                     in: CGRect(x: 0, y: 0, width: inputSize, height: inputSize))
        return pixels
    }

    // MARK: Reporting

    /// Writes the report where it can leave the device without a Mac.
    ///
    /// Documents/ is exposed through UIFileSharingEnabled, so this file shows
    /// up in the Files app beside Clips and comes off over the cable or the
    /// share sheet. The alternative — reading four numbers off a phone screen
    /// and retyping them — is where transcription errors come from.
    @discardableResult
    static func write(_ report: String) -> URL? {
        let documents = FileManager.default.urls(for: .documentDirectory,
                                                 in: .userDomainMask)[0]
        let url = documents.appendingPathComponent("ane-results.txt")
        do {
            try report.write(to: url, atomically: true, encoding: .utf8)
            return url
        } catch {
            return nil
        }
    }

    static func stamp() -> String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        return formatter.string(from: Date())
    }

    static func deviceDescription() -> String {
        let device = UIDevice.current
        return "\(device.model), \(device.systemName) \(device.systemVersion)"
    }

    /// A minimal error type. `Error` is a protocol, and any type can adopt it;
    /// this one exists so failures carry a sentence rather than a code.
    enum HarnessError: LocalizedError {
        case message(String)

        var errorDescription: String? {
            switch self {
            case .message(let text): return text
            }
        }
    }
}

// MARK: - The screen

struct ANEComparisonView: View {

    @State private var report = ""
    @State private var running = false
    @State private var savedTo: URL?

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {

                    Text("Punch list item 1.1")
                        .font(.headline)
                    Text("Runs the four frozen crops through yolo11n four "
                         + "times, changing only which compute units Core ML "
                         + "may use. The spread between them is the Neural "
                         + "Engine's effect on the boxes.")
                        .font(.footnote)
                        .foregroundStyle(.secondary)

                    Button {
                        start()
                    } label: {
                        if running {
                            ProgressView()
                        } else {
                            Text("Run comparison")
                        }
                    }
                    .buttonStyle(.borderedProminent)
                    .disabled(running)

                    if !report.isEmpty {
                        Text(report)
                            .font(.system(.footnote, design: .monospaced))
                            .textSelection(.enabled)

                        if let savedTo {
                            Text("Saved to \(savedTo.lastPathComponent) — "
                                 + "visible in Files under On My iPhone → "
                                 + "GoalKick.")
                                .font(.caption)
                                .foregroundStyle(.secondary)
                            ShareLink(item: savedTo) {
                                Label("Share results", systemImage: "square.and.arrow.up")
                            }
                        }
                    }
                }
                .padding()
            }
            .navigationTitle("ANE check")
        }
    }

    private func start() {
        running = true
        report = ""
        savedTo = nil

        // A Task lets the button repaint as a spinner before the work starts.
        // Everything here is main-actor, which is fine for a harness running
        // sixteen inferences on four small images.
        Task {
            await Task.yield()
            let text = ANEComparison.run()
            report = text
            savedTo = ANEComparison.write(text)
            running = false
            print(text)
        }
    }
}

#Preview {
    ANEComparisonView()
}
