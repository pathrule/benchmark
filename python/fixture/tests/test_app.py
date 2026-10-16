import unittest

from acme import App, Request, Response


class AppTests(unittest.TestCase):
    def test_unknown_option_is_rejected(self):
        with self.assertRaises(TypeError):
            App(colour="blue")

    def test_middleware_wraps_handler(self):
        app = App()
        seen = []

        def tag(request, following):
            seen.append("before")
            response = following(request)
            response.headers["X-Tagged"] = "yes"
            return response

        app.use(tag)
        app.route("/t", lambda req: Response.text("t"))
        response = app.handle(Request("GET", "/t"))
        self.assertEqual(response.headers["X-Tagged"], "yes")
        self.assertEqual(seen, ["before"])

    def test_oversized_headers_answer_431(self):
        app = App(max_header_bytes=10)
        self.assertEqual(app.handle(Request("GET", "/", {"X-Long": "x" * 20})).status, 431)
