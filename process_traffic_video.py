#!/usr/bin/env python3
"""
Script to process a traffic video and display violations on dashboard
Usage: python process_traffic_video.py <video_path>
"""
import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from app import TrafficViolationDetectionSystem


def process_video(video_path):
    """Process a single traffic video"""
    
    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        return False
    
    print(f"\n{'='*60}")
    print(f"Traffic Violation Detection System")
    print(f"{'='*60}")
    print(f"\nVideo: {video_path}")
    print(f"File Size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
    
    # Prepare configuration
    config = {
        'video_path': video_path,
        'detection_model': 'yolov8n.pt',
        'helmet_model': 'models/yolo_helmet.pt',
        'plate_model': 'models/yolo_plate.pt',
        'database_path': 'database/violations.db',
        'output_dir': 'output',
        'screenshot_interval': 5,
        'confidence_threshold': 0.45
    }
    
    # Initialize and run system
    print("\nInitializing detection system...")
    system = TrafficViolationDetectionSystem(config)
    
    print("Starting video processing...")
    stats = system.run(display=False)
    
    print(f"\n{'='*60}")
    print(f"PROCESSING COMPLETED")
    print(f"{'='*60}")
    print(f"Total Frames Processed: {stats.get('total_frames', 0)}")
    print(f"Violations Detected: {len(stats.get('violations', []))}")
    print(f"Output Video: {stats.get('output_video', 'N/A')}")
    print(f"Screenshots Saved: {len([f for f in os.listdir('output/screenshots') if f.endswith(('.jpg', '.png'))])}")
    
    if stats.get('violations'):
        print(f"\nViolations Summary:")
        for i, violation in enumerate(stats.get('violations', [])[:10], 1):
            print(f"  {i}. {violation.get('type', 'Unknown')} - "
                  f"Severity: {violation.get('severity', 'N/A')} - "
                  f"Plate: {violation.get('plate', 'Unknown')}")
        
        if len(stats.get('violations', [])) > 10:
            print(f"  ... and {len(stats.get('violations', [])) - 10} more violations")
    
    print(f"\n{'='*60}")
    print(f"✓ Access the dashboard at: http://localhost:5000")
    print(f"{'='*60}\n")
    
    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Process a traffic video and detect violations',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python process_traffic_video.py data/videos/traffic.mp4
  python process_traffic_video.py path/to/video.avi
        """
    )
    
    parser.add_argument(
        'video_path',
        nargs='?',
        help='Path to the traffic video file to process'
    )
    
    args = parser.parse_args()
    
    if not args.video_path:
        # If no video provided, look for videos in data/videos
        videos_dir = 'data/videos'
        if os.path.exists(videos_dir):
            videos = [f for f in os.listdir(videos_dir) 
                     if f.lower().endswith(('.mp4', '.avi', '.mov', '.mkv'))]
            if videos:
                print(f"Available videos in {videos_dir}:")
                for i, video in enumerate(videos, 1):
                    size = os.path.getsize(os.path.join(videos_dir, video)) / (1024*1024)
                    print(f"  {i}. {video} ({size:.2f} MB)")
                
                choice = input("\nEnter video number to process (or 'q' to quit): ").strip()
                if choice.lower() == 'q':
                    print("Exiting...")
                    return
                
                try:
                    video_path = os.path.join(videos_dir, videos[int(choice) - 1])
                except (ValueError, IndexError):
                    print("Invalid selection")
                    return
            else:
                print(f"No video files found in {videos_dir}")
                print("Usage: python process_traffic_video.py <video_path>")
                return
        else:
            print("Usage: python process_traffic_video.py <video_path>")
            print("Create data/videos folder and place a traffic video file there.")
            return
    else:
        video_path = args.video_path
    
    # Process the video
    success = process_video(video_path)
    
    if success:
        input("\nPress Enter to exit...")


if __name__ == '__main__':
    main()
