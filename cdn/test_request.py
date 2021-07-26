from unittest import TestCase
from cdn import Request
import numpy as np


class TestRequest(TestCase):
    def test_init(self):
        # check empty
        Request()

        # check etc
        for i in range(10):
            length = np.random.randint(1000)
            prob = np.random.random(length)
            prob = prob / np.sum(prob)
            size = np.random.randint(1, 10 * 1000 * 1000, length)
            sizewrong = np.zeros(length)
            probwrong = np.random.random(length)
            Request(size, prob)

            with self.assertRaises(AssertionError):
                Request(size, probwrong)

            with self.assertRaises(AssertionError):
                Request(sizewrong, prob)

            with self.assertRaises(AssertionError):
                Request(np.ones(length + 1), prob)

    def test_contentbase(self):
        # check empty
        request = Request()
        self.assertEqual(request.contentbase, 0)

        # check etc
        for i in range(10):
            length = np.random.randint(1000)
            prob = np.random.random(length)
            prob = prob / np.sum(prob)
            size = np.random.randint(1, 10 * 1000 * 1000, length)
            request = Request(size, prob)
            self.assertEqual(request.contentbase, np.sum(size))

    def test_miss(self):
        # check empty
        request = Request()
        print(request.miss(0))

        # check etc
        for i in range(10):
            length = np.random.randint(1000)
            prob = np.random.random(length)
            prob = prob / np.sum(prob)
            size = np.random.randint(1, 10 * 1000 * 1000, length)
            request = Request(size, prob)

    def test_consistenthashing(self):
        for i in range(10):
            length = np.random.randint(1000)
            prob = np.random.random(length)
            prob = prob / np.sum(prob)
            size = np.random.randint(1, 10 * 1000 * 1000, length)
            request = Request(size, prob)
            request.consistenthashing(5, 2)
