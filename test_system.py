#!/usr/bin/env python3
"""
System Test Script for LAN Communication System
Tests camera, audio, and network functionality
"""

import cv2
import pyaudio
import socket
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox

class SystemTester:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("LAN Communication System - System Test")
        self.root.geometry("600x500")
        
        self.setup_gui()
        
    def setup_gui(self):
        """Setup test GUI"""
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = ttk.Label(main_frame, text="System Test Suite", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Test buttons
        tests_frame = ttk.LabelFrame(main_frame, text="Hardware Tests")
        tests_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(tests_frame, text="Test Camera", 
                  command=self.test_camera).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(tests_frame, text="Test Audio Input", 
                  command=self.test_audio_input).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(tests_frame, text="Test Audio Output", 
                  command=self.test_audio_output).pack(fill=tk.X, padx=10, pady=5)
        
        # Network tests
        network_frame = ttk.LabelFrame(main_frame, text="Network Tests")
        network_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(network_frame, text="Test Network Interface", 
                  command=self.test_network).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(network_frame, text="Test Socket Creation", 
                  command=self.test_sockets).pack(fill=tk.X, padx=10, pady=5)
        
        # Results area
        results_frame = ttk.LabelFrame(main_frame, text="Test Results")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.results_text = tk.Text(results_frame, height=15, state=tk.DISABLED)
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", 
                                 command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        self.results_text.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
        # Run all tests button
        ttk.Button(main_frame, text="Run All Tests", 
                  command=self.run_all_tests).pack(pady=10)
        
    def log_result(self, message):
        """Add result to the text area"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.insert(tk.END, f"{message}\n")
        self.results_text.see(tk.END)
        self.results_text.config(state=tk.DISABLED)
        self.root.update()
        
    def test_camera(self):
        """Test camera functionality"""
        self.log_result("🎥 Testing Camera...")
        
        try:
            # Try to open camera
            cap = cv2.VideoCapture(0)
            
            if not cap.isOpened():
                self.log_result("❌ Camera: Cannot open camera device")
                return False
                
            # Try to read a frame
            ret, frame = cap.read()
            
            if not ret:
                self.log_result("❌ Camera: Cannot read frames from camera")
                cap.release()
                return False
                
            # Get camera properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            
            self.log_result(f"✅ Camera: Working - Resolution: {width}x{height}, FPS: {fps}")
            
            # Test for a few seconds
            self.log_result("   Testing camera for 3 seconds...")
            start_time = time.time()
            frame_count = 0
            
            while time.time() - start_time < 3:
                ret, frame = cap.read()
                if ret:
                    frame_count += 1
                else:
                    break
                    
            actual_fps = frame_count / 3
            self.log_result(f"   Captured {frame_count} frames (avg {actual_fps:.1f} FPS)")
            
            cap.release()
            return True
            
        except Exception as e:
            self.log_result(f"❌ Camera: Error - {str(e)}")
            return False
            
    def test_audio_input(self):
        """Test audio input functionality"""
        self.log_result("🎤 Testing Audio Input...")
        
        try:
            audio = pyaudio.PyAudio()
            
            # Get default input device info
            default_device = audio.get_default_input_device_info()
            self.log_result(f"   Default input device: {default_device['name']}")
            
            # Test audio recording
            chunk = 1024
            format = pyaudio.paInt16
            channels = 1
            rate = 44100
            
            stream = audio.open(
                format=format,
                channels=channels,
                rate=rate,
                input=True,
                frames_per_buffer=chunk
            )
            
            self.log_result("   Recording audio for 2 seconds...")
            
            # Record for 2 seconds
            frames = []
            for i in range(0, int(rate / chunk * 2)):
                data = stream.read(chunk)
                frames.append(data)
                
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            # Analyze audio level
            import numpy as np
            audio_data = np.frombuffer(b''.join(frames), dtype=np.int16)
            max_amplitude = np.max(np.abs(audio_data))
            
            if max_amplitude > 1000:
                self.log_result(f"✅ Audio Input: Working - Max amplitude: {max_amplitude}")
            else:
                self.log_result(f"⚠️  Audio Input: Very quiet - Max amplitude: {max_amplitude}")
                self.log_result("   Try speaking louder or check microphone")
                
            return True
            
        except Exception as e:
            self.log_result(f"❌ Audio Input: Error - {str(e)}")
            return False
            
    def test_audio_output(self):
        """Test audio output functionality"""
        self.log_result("🔊 Testing Audio Output...")
        
        try:
            audio = pyaudio.PyAudio()
            
            # Get default output device info
            default_device = audio.get_default_output_device_info()
            self.log_result(f"   Default output device: {default_device['name']}")
            
            # Generate a test tone
            import numpy as np
            
            sample_rate = 44100
            duration = 1.0  # seconds
            frequency = 440  # Hz (A note)
            
            # Generate sine wave
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            wave = np.sin(frequency * 2 * np.pi * t) * 0.3
            
            # Convert to 16-bit integers
            audio_data = (wave * 32767).astype(np.int16)
            
            # Play the tone
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=sample_rate,
                output=True
            )
            
            self.log_result("   Playing test tone (440 Hz for 1 second)...")
            stream.write(audio_data.tobytes())
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            self.log_result("✅ Audio Output: Test tone played successfully")
            return True
            
        except Exception as e:
            self.log_result(f"❌ Audio Output: Error - {str(e)}")
            return False
            
    def test_network(self):
        """Test network interface"""
        self.log_result("🌐 Testing Network Interface...")
        
        try:
            # Get local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            self.log_result(f"✅ Network: Local IP address: {local_ip}")
            
            # Test hostname resolution
            hostname = socket.gethostname()
            self.log_result(f"   Hostname: {hostname}")
            
            return True
            
        except Exception as e:
            self.log_result(f"❌ Network: Error - {str(e)}")
            return False
            
    def test_sockets(self):
        """Test socket creation and binding"""
        self.log_result("🔌 Testing Socket Creation...")
        
        # Test TCP socket
        try:
            tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcp_socket.bind(('localhost', 0))  # Bind to any available port
            port = tcp_socket.getsockname()[1]
            tcp_socket.close()
            
            self.log_result(f"✅ TCP Socket: Created and bound to port {port}")
            
        except Exception as e:
            self.log_result(f"❌ TCP Socket: Error - {str(e)}")
            return False
            
        # Test UDP socket
        try:
            udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            udp_socket.bind(('localhost', 0))  # Bind to any available port
            port = udp_socket.getsockname()[1]
            udp_socket.close()
            
            self.log_result(f"✅ UDP Socket: Created and bound to port {port}")
            
        except Exception as e:
            self.log_result(f"❌ UDP Socket: Error - {str(e)}")
            return False
            
        # Test specific ports used by the application
        test_ports = [8888, 8889, 8890]
        
        for port in test_ports:
            try:
                test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                test_socket.bind(('localhost', port))
                test_socket.close()
                self.log_result(f"✅ Port {port}: Available")
                
            except Exception as e:
                self.log_result(f"⚠️  Port {port}: In use or blocked - {str(e)}")
                
        return True
        
    def run_all_tests(self):
        """Run all tests sequentially"""
        self.log_result("🚀 Running All System Tests...")
        self.log_result("=" * 50)
        
        tests = [
            ("Camera", self.test_camera),
            ("Audio Input", self.test_audio_input),
            ("Audio Output", self.test_audio_output),
            ("Network", self.test_network),
            ("Sockets", self.test_sockets)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                self.log_result(f"❌ {test_name}: Unexpected error - {str(e)}")
                results[test_name] = False
                
            self.log_result("")  # Add spacing
            
        # Summary
        self.log_result("📊 Test Summary:")
        self.log_result("-" * 30)
        
        passed = 0
        total = len(tests)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log_result(f"{test_name}: {status}")
            if result:
                passed += 1
                
        self.log_result(f"\nOverall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log_result("\n🎉 All tests passed! System is ready for LAN communication.")
        else:
            self.log_result(f"\n⚠️  {total - passed} test(s) failed. Please check the issues above.")
            
    def run(self):
        """Run the test application"""
        self.root.mainloop()

if __name__ == "__main__":
    tester = SystemTester()
    tester.run()