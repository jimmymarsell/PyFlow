import unittest
import logging
import os
from datetime import datetime
from time import sleep
from common.logger import get_logger, setup_log, LOG_DIR

class TestLogger(unittest.TestCase):
    def setUp(self):
        logging.getLogger().handlers.clear()

    def test_get_logger(self):
        logger1 = get_logger("test1")
        logger2 = get_logger("test2")
        self.assertIsNotNone(logger1)
        self.assertIsNotNone(logger2)
        self.assertEqual(logger1.name, "test1")
        self.assertEqual(logger2.name, "test2")

    def test_setup_log_console_only(self):
        logger = setup_log(level=logging.INFO)
        self.assertIsNotNone(logger)
        self.assertEqual(logger.level, logging.INFO)
        self.assertTrue(len(logger.handlers) >= 1)

    def test_setup_log_with_file(self):
        logger = setup_log("test.log", logging.DEBUG)
        self.assertIsNotNone(logger)
        self.assertEqual(logger.level, logging.DEBUG)
        self.assertTrue(len(logger.handlers) >= 2)
        timestamp = datetime.now().strftime("%Y%m%d_%H")
        log_file = os.path.join(LOG_DIR, f"{timestamp}_test.log")
        self.assertTrue(os.path.exists(log_file))

    def test_setup_log_default_level(self):
        logger = setup_log()
        self.assertIsNotNone(logger)
        self.assertEqual(logger.level, logging.INFO)

    def test_log_level_filter(self):
        logger = setup_log("test_level.log", logging.WARNING)
        self.assertEqual(logger.level, logging.WARNING)

    def tearDown(self):
        logger = logging.getLogger()
        for handler in logger.handlers[:]:
            handler.close()
            logger.removeHandler(handler)
        if os.path.exists(LOG_DIR):
            for file in os.listdir(LOG_DIR):
                if "test" in file:
                    os.remove(os.path.join(LOG_DIR, file))
                    try:
                        os.remove(os.path.join(LOG_DIR, file))
                    except PermissionError:
                        pass

if __name__ == "__main__":
    unittest.main()
