import json
import unittest

from acme.problem import TYPE_BASE, problem


class ProblemTests(unittest.TestCase):
    def test_problem_shape(self):
        response = problem(418, "Teapot", "short and stout", "teapot")
        self.assertEqual(response.status, 418)
        self.assertEqual(response.headers["Content-Type"], "application/problem+json")
        body = json.loads(response.body)
        self.assertEqual(body["type"], TYPE_BASE + "teapot")
        self.assertEqual(body["status"], 418)
