import cv2
import argparse
import sys
import os
import time

# Add root folder to sys.path to enable direct imports
root_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from utils import ConfigLoader, logger, FPSCalculator, VideoWriterWrapper
from cv.camera import CameraStream
from pipelines import ModularSafetyPipeline


def main():
    parser = argparse.ArgumentParser(description="FleetGuardian AI - Module 1 Vision Pipeline Demo")
    parser.add_argument("--source", type=str, default=None, help="Camera index (e.g. 0) or RTSP URL or path to video file")
    parser.add_argument("--output", type=str, default=None, help="Optional output path to write annotated video file (.mp4)")
    parser.add_argument("--headless", action="store_true", help="Run without calling cv2.imshow (useful for server/docker environments)")
    parser.add_argument("--max-frames", type=int, default=None, help="Stop execution after processing N frames (useful for test validation)")
    args = parser.parse_args()

    config = ConfigLoader()
    
    # Resolve video source
    source = args.source
    if source is None:
        source = config.get("camera.source", 0)
    
    # Parse source digits to integers for webcam
    if str(source).isdigit():
        source = int(source)

    # Initialize modules
    pipeline = ModularSafetyPipeline()
    fps_calc = FPSCalculator()
    
    # Output file setup
    writer = None
    output_path = args.output
    
    # Initialize Camera
    logger.info("Starting FleetGuardian AI Module 1 vision pipeline...")
    camera = CameraStream(
        source=source,
        width=config.get("camera.width", 640),
        height=config.get("camera.height", 480),
        fps=config.get("camera.fps", 30),
        auto_reconnect=config.get("camera.auto_reconnect", True),
        reconnect_delay=config.get("camera.reconnect_delay", 5.0)
    )

    try:
        camera.start()
        fps_calc.start()
        
        # Wait briefly for camera to start returning frames
        time.sleep(1.0)
        
        frame_count = 0
        logger.info("Pipeline processing active. Press Ctrl+C or 'q' to stop.")

        while camera.running:
            ret, frame = camera.read()
            if not ret or frame is None:
                # If it's a file, we might have hit the end
                if camera.is_file:
                    logger.info("Video playback completed successfully.")
                    break
                
                # Wait briefly and retry
                time.sleep(0.01)
                continue

            frame_count += 1
            
            # Start timing
            fps = fps_calc.update()
            
            # Execute Pipeline
            annotated_frame, metrics, alerts = pipeline.process_frame(frame, fps)
            
            # Print periodic summary
            if frame_count % 30 == 0:
                logger.info(
                    f"Frame {frame_count} | FPS: {fps:.2f} | "
                    f"EAR: {metrics['ear']:.2f} | Drowsy Score: {metrics['drowsiness_score']:.2f} | "
                    f"Distract Score: {metrics['distraction_score']:.2f} | Phone: {metrics['phone_detected']}"
                )
                if alerts:
                    logger.warning(f"Active Alerts: {[a['message'] for a in alerts]}")

            # Set up output video writer on the first frame if output path is specified
            if output_path and writer is None:
                h, w = annotated_frame.shape[:2]
                writer = VideoWriterWrapper(
                    output_path=output_path,
                    fps=config.get("video.output_fps", 30.0),
                    width=w,
                    height=h,
                    codec_name=config.get("video.output_format", "mp4v")
                )
                writer.open()

            # Save frame to output video file
            if writer:
                writer.write(annotated_frame)

            # Display frame
            if not args.headless:
                cv2.imshow("FleetGuardian AI - Module 1 Demo", annotated_frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    logger.info("User requested termination.")
                    break

            # Limit processed frames
            if args.max_frames and frame_count >= args.max_frames:
                logger.info(f"Reached configured limit of {args.max_frames} frames.")
                break

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received.")
    except Exception as e:
        logger.error(f"Pipeline crashed with exception: {e}", exc_info=True)
    finally:
        camera.stop()
        if writer:
            writer.release()
        if not args.headless:
            cv2.destroyAllWindows()
        logger.info("Pipeline terminated and resources cleaned up.")


if __name__ == "__main__":
    main()
