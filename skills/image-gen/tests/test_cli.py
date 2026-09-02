import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class MockHandler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        pass

    def send_json(self, payload):
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/v1/models":
            self.send_json({"data": [{"id": model} for model in self.server.models]})
        elif self.path == "/v1/videos/video-test":
            host, port = self.server.server_address
            self.send_json({"status": "done", "video": {"url": f"http://{host}:{port}/artifact.mp4", "duration": 8}})
        elif self.path == "/artifact.mp4":
            data = b"mock-video"
            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_error(404)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        if self.path == "/v1/videos/generations":
            self.server.video_request = json.loads(raw)
            self.send_json({"request_id": "video-test"})
        elif self.path == "/v1/images/generations":
            self.server.image_request = json.loads(raw)
            payload = 'data: {"data":[{"b64_json":"bW9jay1pbWFnZQ=="}]}\n\ndata: [DONE]\n\n'.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_error(404)


class CliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), MockHandler)
        cls.server.models = ["grok-imagine-image", "gpt-image-2", "grok-imagine-video", "grok-imagine-video-1.5"]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.base_url = f"http://{host}:{port}/v1"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_node_discovers_and_selects_image_model(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "image.png"
            result = subprocess.run([
                "node", str(ROOT / "scripts/node/image-gen.js"),
                "--mode", "text", "--prompt", "test", "--api-key", "test-key",
                "--base-url", self.base_url, "--out", str(output),
            ], text=True, capture_output=True, check=True)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["model"], "gpt-image-2")
            self.assertEqual(self.server.image_request["model"], "gpt-image-2")
            self.assertEqual(output.read_bytes(), b"mock-image")

    def test_python_selects_1080p_video_model_and_default_duration(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "video.mp4"
            result = subprocess.run([
                sys.executable, str(ROOT / "scripts/python/image_gen.py"),
                "--mode", "video", "--prompt", "test", "--resolution", "1080p",
                "--api-key", "test-key", "--base-url", self.base_url, "--out", str(output),
            ], text=True, capture_output=True, check=True)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["model"], "grok-imagine-video-1.5")
            self.assertEqual(self.server.video_request["model"], "grok-imagine-video-1.5")
            self.assertEqual(self.server.video_request["duration"], 8)
            self.assertEqual(output.read_bytes(), b"mock-video")


if __name__ == "__main__":
    unittest.main()
