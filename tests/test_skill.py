import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "skills/seedance-2-0/scripts"))
from seedance_job import API, SeedanceError, build, save


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def read(self):
        return self.payload

    def close(self):
        pass


class SkillTests(unittest.TestCase):
    def test_variant_and_mode_contracts(self):
        text = build("seedance-2.0-mini", "x")
        self.assertEqual(text["model"], "seedance-2.0-mini")
        frame = build(
            "seedance-2.0", "x", mode="first_last_frames",
            start_image="https://cdn.test/start.png", end_image="https://cdn.test/end.png",
            aspect_ratio="adaptive", resolution="4k",
        )
        self.assertEqual(frame["start_image"]["url"], "https://cdn.test/start.png")
        refs = build(
            "seedance-2.0-fast", "x", mode="multimodal_reference",
            reference_images=["https://cdn.test/a.png"],
            reference_videos=["https://cdn.test/a.mp4"],
            aspect_ratio="16:9",
        )
        self.assertEqual(len(refs["reference_images"]), 1)
        self.assertEqual(len(refs["reference_videos"]), 1)

    def test_rejects_wrong_model_duration_and_local_media(self):
        with self.assertRaises(ValueError):
            build("bad", "x")
        with self.assertRaises(ValueError):
            build("seedance-2.0", "x", duration=16)
        with self.assertRaises(ValueError):
            build("seedance-2.0", "x", mode="start_image", start_image="./face.png", aspect_ratio="adaptive")

    def test_api_submit_has_auth_and_user_agent(self):
        seen = []
        def fake_open(request, timeout):
            seen.append(request)
            return FakeResponse(b'{"request_id":"job_1"}')
        with patch("seedance_job.urllib.request.urlopen", side_effect=fake_open):
            job = API("secret", base="https://api.test/v1").submit({"model": "seedance-2.0", "prompt": "x"})
        self.assertEqual(job, "job_1")
        self.assertEqual(seen[0].get_header("Authorization"), "Bearer secret")
        self.assertEqual(seen[0].get_header("User-agent"), "seedance-2-0-skill-codex/1.0")
        self.assertEqual(json.loads(seen[0].data)["model"], "seedance-2.0")

    def test_state_save_is_json_and_download_requires_done(self):
        with tempfile.TemporaryDirectory() as directory:
            path = pathlib.Path(directory) / "job.json"
            save(path, {"request_id": "job_1", "status": "pending"})
            self.assertEqual(json.loads(path.read_text())["request_id"], "job_1")
            with patch("seedance_job.urllib.request.urlopen", return_value=FakeResponse(b'{"status":"pending"}')):
                self.assertEqual(API("secret", base="https://api.test/v1").status("job_1")["status"], "pending")

    def test_status_rejects_unknown_state(self):
        with patch("seedance_job.urllib.request.urlopen", return_value=FakeResponse(b'{"status":"running"}')):
            with self.assertRaises(SeedanceError):
                API("secret", base="https://api.test/v1").status("job_1")


if __name__ == "__main__":
    unittest.main()
