# Architecture Decisions

## Control Channel

*   **Protocol:** JSON messages over TCP.
*   **Framing:** Newline or length-prefixed.
*   **Usage:** `REGISTER`, `CHAT`, file metadata, presenter control.

## File Transfers & Screen Sharing

*   **Protocol:** TCP (for reliability).
*   **Implementation:** File uploads should be chunked with progress reporting.

## Media (Audio/Video)

*   **Protocol:** UDP (for low latency).
*   **Custom Header:**
    *   `stream_type`: (e.g., audio, video)
    *   `seq_num`: Sequence number for ordering.
    *   `timestamp`: For synchronization.
    *   `frame/fragment_id`: To handle fragmentation.
*   **Fragmentation:** Keep UDP payload <= 1200 bytes to avoid IP fragmentation.

## Ports

*   **TCP Control:** 5000
*   **UDP Video:** 5001
*   **UDP Audio:** 5002
*   **TCP File Transfer:** 5003
*   **TCP Screen Sharing:** 5004

*(These will be documented in `protocol.md`)*

## Concurrency Model

*   **Choice:** `asyncio` for scalable I/O or `threading` for a simpler mental model.
*   **Consistency:** The chosen model will be used consistently throughout the project.

## Capture & Codecs

*   **Video:**
    *   **Capture:** OpenCV.
    *   **Prototype Codec:** JPEG or MJPEG.
    *   **Future Codec:** H.264.
*   **Audio:**
    *   **Capture/Playback:** `sounddevice` or `PyAudio`.
    *   **Future Codec:** Opus.
