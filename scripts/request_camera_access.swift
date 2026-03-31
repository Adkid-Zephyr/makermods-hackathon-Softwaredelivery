import AVFoundation
import Foundation

func describe(_ status: AVAuthorizationStatus) -> String {
    switch status {
    case .authorized:
        return "authorized"
    case .denied:
        return "denied"
    case .restricted:
        return "restricted"
    case .notDetermined:
        return "not_determined"
    @unknown default:
        return "unknown"
    }
}

let before = AVCaptureDevice.authorizationStatus(for: .video)
print("camera_auth_before \(describe(before)) \(before.rawValue)")

let semaphore = DispatchSemaphore(value: 0)

AVCaptureDevice.requestAccess(for: .video) { granted in
    let after = AVCaptureDevice.authorizationStatus(for: .video)
    print("camera_request_granted \(granted)")
    print("camera_auth_after \(describe(after)) \(after.rawValue)")
    semaphore.signal()
}

if semaphore.wait(timeout: .now() + 20) == .timedOut {
    let current = AVCaptureDevice.authorizationStatus(for: .video)
    print("camera_request_timed_out true")
    print("camera_auth_current \(describe(current)) \(current.rawValue)")
    exit(current == .authorized ? 0 : 1)
}

exit(AVCaptureDevice.authorizationStatus(for: .video) == .authorized ? 0 : 1)
