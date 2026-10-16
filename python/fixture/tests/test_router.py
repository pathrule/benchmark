import unittest

from acme import App, Request, Response


class RouterTests(unittest.TestCase):
    def test_exact_path_matches(self):
        app = App()
        app.route("/a", lambda req: Response.text("a"))
        self.assertEqual(app.handle(Request("GET", "/a")).body, b"a")

    def test_unknown_path_is_404(self):
        app = App()
        self.assertEqual(app.handle(Request("GET", "/nope")).status, 404)

    def test_methods_option_restricts(self):
        app = App()
        app.route("/only-post", lambda req: Response.text("ok"), methods=["POST"])
        self.assertEqual(app.handle(Request("GET", "/only-post")).status, 404)
        self.assertEqual(app.handle(Request("POST", "/only-post")).status, 200)

    def test_unknown_route_option_is_rejected(self):
        app = App()
        with self.assertRaises(TypeError):
            app.route("/x", lambda req: Response.text("x"), colour="blue")
